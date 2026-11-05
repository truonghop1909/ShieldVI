"""Refine a frozen ViSoBERT classifier on labeled train data, never demo labels.

The deployment threshold stays 0.41. Validation chooses among head candidates;
official test is opened for scoring only after selection, once. A failed gate
leaves the baseline in service. Source checkpoints are never overwritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import csv
import hashlib
import json
from pathlib import Path
import random
import re
import time
import unicodedata

THRESHOLD = 0.41


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text).casefold()).strip()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path, with_labels=True):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    result = []
    for index, row in enumerate(rows):
        text = row.get('Comment', '').strip()
        if not text:
            raise ValueError(f'Empty text: {path}:{index+2}')
        label = int(row['Toxicity']) if with_labels else None
        if with_labels and label not in (0, 1):
            raise ValueError('Labels must be original binary Toxicity annotations')
        result.append({'id': row.get('', str(index)), 'text': text, 'label': label})
    return result


def clean_train(rows, held_out_texts):
    blocked = {normalize(t) for t in held_out_texts}
    groups = {}
    for row in rows:
        groups.setdefault(normalize(row['text']), []).append(row)
    kept = []
    counts = Counter(overlap_removed=0, conflicting_removed=0, duplicates_removed=0)
    for key, group in groups.items():
        if key in blocked:
            counts['overlap_removed'] += len(group)
        elif len({r['label'] for r in group}) > 1:
            counts['conflicting_removed'] += len(group)
        else:
            kept.append(group[0])
            counts['duplicates_removed'] += len(group) - 1
    return kept, dict(counts)


def metrics(labels, probabilities, threshold=THRESHOLD):
    if len(labels) != len(probabilities) or not labels:
        raise ValueError('Nonempty labels/probabilities must have the same length')
    tp = fp = tn = fn = 0
    brier = log_loss = 0.0
    import math
    for label, probability in zip(labels, probabilities):
        if label not in (0, 1) or not 0 <= probability <= 1:
            raise ValueError('Invalid label/probability')
        positive = probability >= threshold
        tp += int(label == 1 and positive)
        fp += int(label == 0 and positive)
        tn += int(label == 0 and not positive)
        fn += int(label == 1 and not positive)
        brier += (probability - label) ** 2
        p = min(1 - 1e-7, max(1e-7, probability))
        log_loss -= label * math.log(p) + (1-label) * math.log(1-p)
    divide = lambda a, b: a / b if b else 0.0
    return {
        'n': len(labels), 'threshold': threshold, 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
        'macro_f1': (divide(2*tp, 2*tp+fp+fn) + divide(2*tn, 2*tn+fp+fn)) / 2,
        'toxic_precision': divide(tp, tp+fp), 'toxic_recall': divide(tp, tp+fn),
        'accuracy': (tp+tn)/len(labels), 'brier': brier/len(labels), 'log_loss': log_loss/len(labels),
    }


def validation_gate(baseline, candidate):
    return (candidate['macro_f1'] >= baseline['macro_f1'] + 0.005 and
            candidate['toxic_precision'] >= baseline['toxic_precision'] and
            candidate['toxic_recall'] >= baseline['toxic_recall'])


def test_gate(baseline, candidate):
    # Test is a final audit, not another selection loop.
    return (candidate['macro_f1'] >= baseline['macro_f1'] and
            candidate['toxic_precision'] >= baseline['toxic_precision'] - 0.02 and
            candidate['toxic_recall'] >= baseline['toxic_recall'] - 0.02)


def precision_tradeoff_gate(baseline, candidate):
    """An explicit alternate validation objective for reducing false alarms.

    Allow at most 0.5 percentage-point macro-F1 loss and 3 points of recall loss,
    require better precision and at least 0.25% of all validation rows fewer FPs.
    The unchanged final test audit still must pass before deployment.
    """
    return (candidate['fp'] <= baseline['fp'] - max(1, baseline['n'] * 0.0025) and
            candidate['macro_f1'] >= baseline['macro_f1'] - 0.005 and
            candidate['toxic_precision'] >= baseline['toxic_precision'] and
            candidate['toxic_recall'] >= baseline['toxic_recall'] - 0.03)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(args):
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    started = time.monotonic()
    torch.set_num_threads(args.threads)
    random.seed(20261029)
    torch.manual_seed(20261029)
    output = Path(args.output).resolve()
    if (output / 'model.safetensors').exists():
        raise ValueError('Refusing to overwrite an existing checkpoint; choose a new --output')
    output.mkdir(parents=True, exist_ok=True)
    cache = output / '.cache'
    cache.mkdir(exist_ok=True)
    train = read_rows(args.train)
    valid = read_rows(args.valid)
    # Test text is used solely to block train overlap; labels remain unopened here.
    test_text_only = read_rows(args.test, with_labels=False)
    train, cleaning = clean_train(train, [r['text'] for r in valid + test_text_only])
    sources = {key: {'path': str(Path(getattr(args, key)).resolve()), 'sha256': file_hash(getattr(args, key))}
               for key in ('train', 'valid', 'test')}
    checkpoint = Path(args.base_model).resolve()
    weight_hash = file_hash(checkpoint / 'model.safetensors')
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint), local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint), local_files_only=True)
    if model.config.num_labels != 2 or not hasattr(model, 'roberta'):
        raise ValueError('Expected a binary XLM-R/ViSoBERT sequence classifier')
    model.eval()
    for parameter in model.roberta.parameters():
        parameter.requires_grad = False
    original_head = copy.deepcopy(model.classifier).eval()

    def features(rows, split):
        key = hashlib.sha256((weight_hash + '\n' + '\n'.join(r['text'] for r in rows) + '\nmax_length=128').encode()).hexdigest()
        destination = cache / f'{split}_{key[:20]}.pt'
        if destination.exists():
            return torch.load(destination, map_location='cpu', weights_only=True)
        # Bucketing by length avoids padding every batch to 128 tokens on CPU.
        # Restore input order before scoring; no labels participate in bucketing.
        order = sorted(range(len(rows)), key=lambda i: len(rows[i]['text']))
        values = torch.empty((len(rows), model.config.hidden_size), dtype=torch.float32)
        with torch.inference_mode():
            for start in range(0, len(rows), 32):
                ids = order[start:start+32]
                tokens = tokenizer([rows[i]['text'] for i in ids], padding=True,
                                   truncation=True, max_length=128, return_tensors='pt')
                values[ids] = model.roberta(**tokens).last_hidden_state[:, 0, :].cpu()
                if start % 256 == 0:
                    print(f'features {split}: {min(start+32,len(rows))}/{len(rows)}', flush=True)
        torch.save(values, destination)
        return values

    def probabilities(head, embeddings):
        head.eval()
        with torch.no_grad():
            return torch.cat([head(batch[:, None, :]).softmax(-1)[:, 1]
                              for batch in embeddings.split(256)]).tolist()

    x_valid = features(valid, 'valid')
    y_valid = [r['label'] for r in valid]
    baseline_valid_probs = probabilities(original_head, x_valid)
    baseline_valid = metrics(y_valid, baseline_valid_probs)
    print('BASELINE_VALID', json.dumps(baseline_valid), flush=True)
    x_train = features(train, 'train')
    y_train = torch.tensor([r['label'] for r in train], dtype=torch.long)
    # inference_mode tensors cannot be saved for autograd by Linear layers.
    x_train = x_train.clone()
    experiments, best_state, best_record = [], None, None
    selection_gate = precision_tradeoff_gate if args.validation_policy == 'precision-noninferiority' else validation_gate
    with torch.no_grad():
        teacher_logits = torch.cat([original_head(batch[:, None, :]) for batch in x_train.split(256)])
    distillation_weight = args.distillation_weight
    for learning_rate in args.learning_rates:
        for positive_weight in args.positive_weights:
            torch.manual_seed(20261029)
            head = copy.deepcopy(original_head)
            optimizer = torch.optim.AdamW(head.parameters(), lr=learning_rate, weight_decay=0.01)
            loss_fn = torch.nn.CrossEntropyLoss(weight=torch.tensor([1.0, positive_weight]))
            for epoch in range(1, args.epochs + 1):
                head.train()
                order = torch.randperm(len(train))
                for ids in order.split(64):
                    optimizer.zero_grad(set_to_none=True)
                    logits = head(x_train[ids, None, :])
                    loss = loss_fn(logits, y_train[ids])
                    if distillation_weight:
                        temperature = 2.0
                        loss = loss + distillation_weight * temperature**2 * torch.nn.functional.kl_div(
                            (logits/temperature).log_softmax(-1),
                            (teacher_logits[ids]/temperature).softmax(-1), reduction='batchmean')
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(head.parameters(), 1.0)
                    optimizer.step()
                scores = metrics(y_valid, probabilities(head, x_valid))
                record = {'lr': learning_rate, 'positive_weight': positive_weight,
                          'epoch': epoch, 'distillation_weight': distillation_weight, 'validation': scores,
                          'passes_validation_gate': selection_gate(baseline_valid, scores),
                          'passes_strict_improvement_gate': validation_gate(baseline_valid, scores)}
                experiments.append(record)
                print('CANDIDATE', json.dumps(record), flush=True)
                if record['passes_validation_gate'] and (best_record is None or scores['macro_f1'] > best_record['validation']['macro_f1']):
                    best_record = record
                    best_state = copy.deepcopy(head.state_dict())
    report = {
        'schema_version': 1, 'seed': 20261029, 'threshold': THRESHOLD,
        'method': 'Frozen ViSoBERT encoder; supervised classifier-head refinement on original ViCTSD train labels.',
        'baseline_checkpoint': str(checkpoint), 'baseline_weights_sha256': weight_hash,
        'data_sources': sources, 'train_cleaning': cleaning,
        'train_count': len(train), 'train_toxic': int(y_train.sum()),
        'validation_policy': args.validation_policy,
        'validation_count': len(valid), 'baseline_validation': baseline_valid,
        'validation_experiments': experiments, 'selected': best_record,
        'status': 'no_candidate_passed_validation',
        'limitations': ['Validation selects hyperparameters; official test is a final single audit.',
                       'No synthetic or suggested demo labels are used for training.',
                       'ViCTSD comment toxicity does not establish conversation harassment or slang-domain accuracy.'],
    }
    if best_state is not None:
        # Selection has finished; now read official test labels for one final audit.
        test = read_rows(args.test)
        x_test = features(test, 'test')
        y_test = [r['label'] for r in test]
        baseline_test_probs = probabilities(original_head, x_test)
        model.classifier.load_state_dict(best_state)
        candidate_test_probs = probabilities(model.classifier, x_test)
        report['baseline_test'] = metrics(y_test, baseline_test_probs)
        report['candidate_test'] = metrics(y_test, candidate_test_probs)
        passed = test_gate(report['baseline_test'], report['candidate_test'])
        report['status'] = 'approved' if passed else 'rejected_by_test_audit'
        with (output / 'test_predictions.csv').open('w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['row_id', 'gold_toxicity', 'baseline_probability', 'candidate_probability'])
            writer.writerows((r['id'], r['label'], b, c) for r, b, c in zip(test, baseline_test_probs, candidate_test_probs))
        if args.diagnostic:
            diagnostic = json.loads(Path(args.diagnostic).read_text(encoding='utf-8-sig'))
            rows = [{'text': c['text']} for c in diagnostic['comments']]
            x_diag = features(rows, 'diagnostic')
            before = probabilities(original_head, x_diag)
            after = probabilities(model.classifier, x_diag)
            report['diagnostic_not_gold'] = [
                {'comment_id': c['comment_id'], 'text': c['text'], 'baseline_probability': b,
                 'candidate_probability': a, 'baseline_flag': b >= THRESHOLD, 'candidate_flag': a >= THRESHOLD}
                for c, b, a in zip(diagnostic['comments'], before, after)
            ]
        # Export an isolated candidate, even if the audit rejects it. Never activate a rejected candidate.
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
    parser.add_argument('--diagnostic')
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--learning-rates', type=float, nargs='+', default=[0.0001, 0.0003])
    parser.add_argument('--positive-weights', type=float, nargs='+', default=[1.0, 2.0])
    parser.add_argument('--epochs', type=int, default=6)
    parser.add_argument('--distillation-weight', type=float, default=0.0)
    parser.add_argument('--validation-policy', choices=['strict-improvement', 'precision-noninferiority'], default='strict-improvement')
    run(parser.parse_args())
