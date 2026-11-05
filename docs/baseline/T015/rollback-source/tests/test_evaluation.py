import pytest
from scripts.evaluate_social_policy import binary_metrics,latency,wilson


def test_metrics_confusion_and_rates_have_known_nonperfect_answer():
    result=binary_metrics([0,0,0,1,1,1],[0,0,1,0,1,1])
    assert result['confusion_matrix']==[[2,1],[1,2]]
    assert result['precision']==result['recall']==result['macro_f1']==pytest.approx(2/3)
    assert result['false_positive_rate']==pytest.approx(1/3)
    lo,hi=result['fpr_wilson_95']
    assert 0<=lo<1/3<hi<=1


def test_no_positive_predictions_is_not_perfect_precision():
    result=binary_metrics([0,1],[0,0])
    assert result['precision'] is None and result['recall']==0
    assert result['false_negative_rate']==1 and result['macro_f1']==pytest.approx(1/3)


@pytest.mark.parametrize('labels,predictions',[([],[]),([0],[1,0]),([0],[2]),([True],[1])])
def test_invalid_evaluation_labels_fail_closed(labels,predictions):
    with pytest.raises(ValueError):binary_metrics(labels,predictions)


def test_empty_intervals_and_latency_are_not_false_zero_measurements():
    assert wilson(0,0) is None
    assert latency([])['median_ms'] is None
    assert latency([10,1,5,2])['median_ms']==3.5
