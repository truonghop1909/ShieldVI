import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluate_synthetic_signals import classification,grounding_metrics

def test_abstention_counts_as_a_miss_and_uncertain_reference_is_separate():
    m=classification([('CLEAN','CLEAN'),('TOXIC','UNCERTAIN'),('UNCERTAIN','TOXIC')])
    assert m['n']==2 and m['coverage']==.5 and m['abstained_toxic']==1 and m['toxic_recall']==0
    assert m['macro_f1']==.5

def test_fp_fn_and_macro_f1_are_symmetric_for_binary_errors():
    m=classification([('CLEAN','CLEAN'),('TOXIC','TOXIC'),('CLEAN','TOXIC'),('TOXIC','CLEAN')])
    assert (m['tp'],m['fp'],m['tn'],m['fn'])==(1,1,1,1) and m['macro_f1']==.5

def test_reference_repeated_events_normalize_timezone_offsets():
    truth={('thread','a'):{'label':'TOXIC','actor':'actor','target':'victim','time':'2020-01-01T00:00:00Z'},
           ('thread','b'):{'label':'TOXIC','actor':'actor','target':'victim','time':'2020-01-01T07:00:00+07:00'}}
    assert grounding_metrics([],truth)['repeated']['fn']==0
