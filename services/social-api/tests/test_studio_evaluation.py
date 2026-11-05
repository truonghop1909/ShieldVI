import json
from uuid import uuid4
import pytest
from test_studio_datasets import studio,payload,sample,upload
from test_live_api import live
from ml_studio.evaluation import EvaluationJobs,EvaluationInput
from pydantic import ValidationError

def test_evaluation_scope_cannot_choose_train_split_or_custom_threshold():
    for changes in ({'split':'train'},{'threshold':.2},{'processor':'v6.2'},{'models':['x']}):
        with pytest.raises(ValidationError):EvaluationInput.model_validate({'dataset_version':'a'*24,'models':['v1','candidate'],**changes})

def test_promotion_denied_server_side_even_for_admin(studio):
    c,owner,_,staff,_,_=studio[0]
    assert c.post('/api/studio/models/candidate/promote',headers=owner).status_code==403
    result=c.post('/api/studio/models/candidate/promote',headers=staff)
    assert result.status_code==409 and 'independent human gold' in result.text

def test_registry_uninitialized_fails_closed_and_never_activates(studio):
    c,_,_,staff,_,_=studio[0]
    assert c.get('/api/studio/models',headers=staff).status_code==503
    assert c.post('/api/studio/evaluations',headers=staff,json={'dataset_version':'a'*24,'models':['v1','candidate']}).status_code==422

def test_registry_pointer_traversal_and_hash_mutation_rejected(studio):
    store=studio[1];root=store.root/'registry';root.mkdir();pointer=root/'latest.json'
    pointer.write_text(json.dumps({'file':'../../outside','sha256':'x'}))
    with pytest.raises(ValueError,match='pointer'):EvaluationJobs(store).catalog()
    (root/'snapshot.json').write_text('{}');pointer.write_text(json.dumps({'file':'snapshot.json','sha256':'wrong'}))
    with pytest.raises(ValueError,match='hash'):EvaluationJobs(store).catalog()
