"""CPU-friendly last-encoder-block refinement with the same untouched holdout gates.

Cache the first eleven frozen blocks' token representations. Optimize only the
last block and classifier on original training labels, with V1 distillation.
Neither demo suggestions nor ViHOS span-proxy labels enter this experiment.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import time

from refine_model import (THRESHOLD, clean_train, file_hash, metrics, read_rows,
                          test_gate, validation_gate, write_json)


def run(args):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from torch.nn.utils.rnn import pad_sequence

    started = time.monotonic()
    torch.set_num_threads(args.threads)
    torch.manual_seed(20261029)
    output = Path(args.output).resolve()
    if (output / 'model.safetensors').exists():
        raise ValueError('Refusing to overwrite an existing exported checkpoint')
    cache = output / '.cache'
    cache.mkdir(parents=True, exist_ok=True)
    checkpoint = Path(args.base_model).resolve()
    weight_hash = file_hash(checkpoint / 'model.safetensors')
    valid = read_rows(args.valid)
    test_text_only = read_rows(args.test, with_labels=False)
    train, cleaning = clean_train(read_rows(args.train), [r['text'] for r in valid + test_text_only])
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint), local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint), local_files_only=True).eval()
    for p in model.parameters():
        p.requires_grad = False
    original_block = model.roberta.encoder.layer[-1]
    original_head = model.classifier

    def encode(rows, split):
        key = hashlib.sha256((weight_hash + '\nlast-block-input\n' + '\n'.join(r['text'] for r in rows)).encode()).hexdigest()
        destination = cache / f'prelast_{split}_{key[:20]}.pt'
        if destination.exists():
            return torch.load(destination, map_location='cpu', weights_only=True)
        order = sorted(range(len(rows)), key=lambda i: len(rows[i]['text']))
        hidden = [None] * len(rows)
        teacher_logits = torch.empty((len(rows), 2))
        captured = []
        hook = original_block.register_forward_pre_hook(lambda module, inputs: captured.append(inputs[0]))
        try:
            with torch.inference_mode():
                for start in range(0, len(rows), 32):
                    ids = order[start:start+32]
                    tokens = tokenizer([rows[i]['text'] for i in ids], truncation=True,
                                       padding=True, max_length=128, return_tensors='pt')
                    teacher_logits[ids] = model(**tokens).logits
                    lengths = tokens['attention_mask'].sum(-1).tolist()
                    for j, (i, length) in enumerate(zip(ids, lengths)):
                        hidden[i] = captured[-1][j, :length].cpu().clone()
                    captured.clear()
                    if start % 256 == 0:
                        print(f'prelast {split}: {min(start+32,len(rows))}/{len(rows)}', flush=True)
        finally:
            hook.remove()
        result = {'hidden': hidden, 'teacher_logits': teacher_logits}
        torch.save(result, destination)
        return result

    def forward(block, head, hidden, ids):
        tensors = [hidden[i] for i in ids]
        padded = pad_sequence(tensors, batch_first=True).clone()
        positions = torch.arange(padded.shape[1])[None, :]
        lengths = torch.tensor([len(t) for t in tensors])[:, None]
        mask = (positions >= lengths).to(padded.dtype)[:, None, None, :] * torch.finfo(padded.dtype).min
        return head(block(padded, attention_mask=mask)[0])

    def score(block, head, encoded):
        block.eval()
        head.eval()
        hidden = encoded['hidden']
        order = sorted(range(len(hidden)), key=lambda i: len(hidden[i]))
        probabilities = [0.0] * len(hidden)
        with torch.no_grad():
            for start in range(0, len(hidden), 32):
                ids = order[start:start+32]
                values = forward(block, head, hidden, ids).softmax(-1)[:, 1].tolist()
                for i, value in zip(ids, values):
                    probabilities[i] = value
        return probabilities

    x_valid = encode(valid, 'valid')
    y_valid = [r['label'] for r in valid]
    baseline_valid = metrics(y_valid, x_valid['teacher_logits'].softmax(-1)[:, 1].tolist())
    # Verify that the cached-block route reproduces real model inference before training.
    probe = {'hidden': x_valid['hidden'][:32], 'teacher_logits': x_valid['teacher_logits'][:32]}
    direct = probe['teacher_logits'].softmax(-1)[:, 1].tolist()
    cached = score(original_block, original_head, probe)
    parity_error = max(abs(a-b) for a, b in zip(direct, cached))
    if parity_error > 0.00001:
        raise ValueError(f'Cached block inference changed predictions: {parity_error}')
    print('BASELINE_VALID', json.dumps(baseline_valid), 'parity', parity_error, flush=True)
    x_train = encode(train, 'train')
    y_train = torch.tensor([r['label'] for r in train])
    teacher = x_train['teacher_logits'].clone()
    experiments, best_state, best_record = [], None, None
    for learning_rate in (0.000002, 0.000005):
        torch.manual_seed(20261029)
        block = copy.deepcopy(original_block)
        head = copy.deepcopy(original_head)
        for p in list(block.parameters()) + list(head.parameters()):
            p.requires_grad = True
        optimizer = torch.optim.AdamW([
            {'params': block.parameters(), 'lr': learning_rate},
            {'params': head.parameters(), 'lr': 0.00001},
        ], weight_decay=0.01)
        loss_fn = torch.nn.CrossEntropyLoss(weight=torch.tensor([1.0, 1.25]))
        order = torch.randperm(len(train)).tolist()
        # Length-bucket shuffled groups to reduce CPU padding during gradients.
        batches = []
        for start in range(0, len(order), 512):
            group = sorted(order[start:start+512], key=lambda i: len(x_train['hidden'][i]))
            batches.extend([group[i:i+32] for i in range(0, len(group), 32)])
        for step, ids in enumerate(batches, 1):
            block.train()
            head.train()
            optimizer.zero_grad(set_to_none=True)
            logits = forward(block, head, x_train['hidden'], ids)
            loss = loss_fn(logits, y_train[ids]) + 2.0 * 4.0 * torch.nn.functional.kl_div(
                (logits/2).log_softmax(-1), (teacher[ids]/2).softmax(-1), reduction='batchmean')
            loss.backward()
            torch.nn.utils.clip_grad_norm_(list(block.parameters()) + list(head.parameters()), 1.0)
            optimizer.step()
            if step % 25 == 0:
                print(f'train last-block lr={learning_rate}: {step}/{len(batches)}', flush=True)
            if step in {len(batches)//2, len(batches)}:
                scores = metrics(y_valid, score(block, head, x_valid))
                record = {'block_lr': learning_rate, 'head_lr': 0.00001, 'step': step,
                          'positive_weight': 1.25, 'distillation_weight': 2.0,
                          'validation': scores, 'passes_validation_gate': validation_gate(baseline_valid, scores)}
                experiments.append(record)
                print('CANDIDATE', json.dumps(record), flush=True)
                if record['passes_validation_gate'] and (best_record is None or scores['macro_f1'] > best_record['validation']['macro_f1']):
                    best_record = record
                    best_state = (copy.deepcopy(block.state_dict()), copy.deepcopy(head.state_dict()))
    report = {
        'schema_version': 1, 'seed': 20261029, 'threshold': THRESHOLD,
        'method': 'Frozen first eleven encoder blocks; supervised last-block + classifier refinement with V1 distillation.',
        'baseline_checkpoint': str(checkpoint), 'baseline_weights_sha256': weight_hash,
        'data_sources': {key: {'path': str(Path(getattr(args, key)).resolve()), 'sha256': file_hash(getattr(args, key))} for key in ('train', 'valid', 'test')},
        'train_cleaning': cleaning, 'train_count': len(train), 'validation_count': len(valid),
        'baseline_validation': baseline_valid, 'cache_parity_max_error': parity_error,
        'validation_experiments': experiments, 'selected': best_record,
        'status': 'no_candidate_passed_validation',
        'limitations': ['No synthetic, suggested demo or ViHOS proxy labels used for training.',
                       'ViCTSD comment toxicity does not establish conversation harassment or slang-domain accuracy.',
                       'Official test labels are not used to choose candidates.'],
    }
    if best_state is not None:
        test = read_rows(args.test)
        x_test = encode(test, 'test')
        model.roberta.encoder.layer[-1].load_state_dict(best_state[0])
        model.classifier.load_state_dict(best_state[1])
        before = x_test['teacher_logits'].softmax(-1)[:, 1].tolist()
        after = score(model.roberta.encoder.layer[-1], model.classifier, x_test)
        report['baseline_test'] = metrics([r['label'] for r in test], before)
        report['candidate_test'] = metrics([r['label'] for r in test], after)
        report['status'] = 'approved' if test_gate(report['baseline_test'], report['candidate_test']) else 'rejected_by_test_audit'
        with (output / 'test_predictions.csv').open('w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['row_id','gold_toxicity','baseline_probability','candidate_probability'])
            writer.writerows((r['id'],r['label'],b,a) for r,b,a in zip(test,before,after))
        model.save_pretrained(str(output), safe_serialization=True)
        tokenizer.save_pretrained(str(output))
        write_json(output / 'threshold_config.json', {
            'threshold': THRESHOLD, 'model_version': 'ViSoBERT V1.1 — ViCTSD',
            'selected_on': 'ViCTSD validation', 'source_checkpoint': str(checkpoint),
            'approval_status': report['status'], 'report': 'refinement_report.json',
        })
    report['elapsed_seconds'] = round(time.monotonic() - started, 2)
    write_json(output / 'refinement_report.json', report)
    print('RESULT', report['status'], str(output / 'refinement_report.json'), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-model', 'train', 'valid', 'test', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--threads', type=int, default=6)
    run(parser.parse_args())
