"""Opt-in local model loading with integrity checks and baseline fallback.

Not imported by main.py; never changes MODEL_PATH, writes DB, or activates a model.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path

class RegistryError(ValueError):pass

class LocalModelRegistry:
    def __init__(self,manifest):
        self.manifest=json.loads(Path(manifest).read_text(encoding='utf-8'))
        if self.manifest.get('schema_version')!=1 or self.manifest.get('threshold')!=.41:
            raise RegistryError('Unsupported registry or threshold')
        self.models=self.manifest['models'];self.fallback=self.manifest['fallback']
        if self.models[self.fallback]['role']!='baseline':raise RegistryError('Fallback must be the original baseline')

    def verify(self,model_id):
        entry=self.models[model_id];path=Path(entry['path'])
        if entry['threshold']!=.41:raise RegistryError('Model threshold differs from baseline')
        hashes=entry['sha256']
        if not {'model.safetensors','config.json','threshold_config.json','tokenizer_config.json'}<=set(hashes):
            raise RegistryError('Missing required artifact hashes')
        for name,sha in hashes.items():
            if Path(name).name!=name:raise RegistryError('Artifact name must be a basename')
            if hashlib.sha256((path/name).read_bytes()).hexdigest()!=sha:raise RegistryError('Checkpoint integrity mismatch')
        if json.loads((path/'threshold_config.json').read_text(encoding='utf-8'))['threshold']!=.41:
            raise RegistryError('Checkpoint threshold mismatch')
        return str(path)

    def load(self,model_id,*,shadow=False,loader=None):
        if model_id not in self.models:raise RegistryError('Model not registered')
        requested=self.models[model_id]
        if not shadow and requested.get('approved_for_selection') is not True:
            raise RegistryError('Unapproved model requires explicit local shadow mode')
        if loader is None:
            from .predictor import ViSoBERTPredictor
            loader=ViSoBERTPredictor
        chosen=model_id;failure=None
        try:predictor=loader(self.verify(model_id))
        except (OSError,ValueError,RuntimeError) as exc:
            if model_id==self.fallback:raise
            failure=type(exc).__name__;chosen=self.fallback
            predictor=loader(self.verify(chosen))
        if predictor.threshold!=.41:raise RegistryError('Loaded predictor threshold mismatch')
        return predictor,{'requested':model_id,'selected':chosen,'shadow':shadow,'fallback_used':chosen!=model_id,
            'failure_type':failure,'production_changed':False}

    def shadow_compare(self,baseline,candidate,texts):
        left=baseline.predict_scores(texts);right=candidate.predict_scores(texts)
        if len(left)!=len(texts) or len(right)!=len(texts):raise RegistryError('Invalid shadow score count')
        if any(not isinstance(v,(float,int)) or not math.isfinite(v) or not 0<=v<=1 for v in left+right):
            raise RegistryError('Invalid shadow probabilities')
        return {'baseline_scores':left,'candidate_scores':right,'threshold':.41,'production_changed':False}
