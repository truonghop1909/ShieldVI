"""V1 toxicity model adapter. Imports expensive ML packages only when model is loaded."""
import json
import os
from pathlib import Path

REFINED_MODEL_PATH = Path(__file__).resolve().parents[1] / 'models' / 'visobert_head_refined'

class ViSoBERTPredictor:
    def __init__(self, model_path: str):
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch

        path = Path(model_path)
        if not path.is_dir():
            raise FileNotFoundError(f"Không tìm thấy checkpoint: {path}")
        self.tokenizer = AutoTokenizer.from_pretrained(str(path), use_fast=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(str(path))
        if self.model.config.num_labels != 2:
            raise ValueError("Checkpoint phải có đúng 2 nhãn (0=clean, 1=toxic)")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device).eval()
        self.torch = torch
        self.name = "ViSoBERT V1 — ViCTSD"
        config_file = path / "threshold_config.json"
        if config_file.exists():
            with config_file.open(encoding="utf-8") as f:
                threshold_data = json.load(f)
            self.threshold = float(threshold_data["threshold"])
            version = threshold_data.get('model_version')
            if version:
                self.name = version if version.startswith('ViSoBERT') else f'ViSoBERT {version} — ViCTSD'
        else:
            self.threshold = 0.41
        if not 0 < self.threshold < 1:
            raise ValueError("Ngưỡng toxicity ngoài khoảng (0, 1)")

    def predict_scores(self, texts: list[str]) -> list[float]:
        scores: list[float] = []
        for start in range(0, len(texts), 16):
            batch = texts[start:start+16]
            tokenized = self.tokenizer(
                batch, return_tensors="pt", truncation=True,
                padding=True, max_length=128,
            ).to(self.device)
            with self.torch.inference_mode():
                logits = self.model(**tokenized).logits
                values = self.torch.softmax(logits, dim=-1)[:, 1]
            scores.extend(float(v) for v in values.cpu().tolist())
        return scores


def default_model_path() -> str:
    explicit = os.environ.get('MODEL_PATH')
    if explicit:
        return explicit
    config = REFINED_MODEL_PATH / 'threshold_config.json'
    if config.is_file() and (REFINED_MODEL_PATH / 'model.safetensors').is_file():
        settings = json.loads(config.read_text(encoding='utf-8'))
        if settings.get('approval_status') == 'approved':
            return str(REFINED_MODEL_PATH)
    return '/content/drive/MyDrive/visobert_toxic_final'
