"""Regression checks for the demo D acceptance gate; no model/server needed."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    'demo_social', Path(__file__).resolve().parents[1] / 'scripts/demo_social.py'
)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


@pytest.mark.parametrize('ids', [None, [], ['c1'], ['c1', 'c1']])
def test_demo_rejects_missing_or_insufficient_comment_ids(ids):
    ai = {'suspected_repeated_harassment': True, 'evidence': [
        {'n_distinct_timestamps': 2, 'evidence_comment_ids': ids}
    ]}
    with pytest.raises(AssertionError, match='Missing or insufficient evidence_comment_ids'):
        demo.assert_repeated_evidence(ai)


def test_demo_requires_ids_on_the_repeated_evidence():
    ai = {'suspected_repeated_harassment': True, 'evidence': [
        {'n_distinct_timestamps': 2, 'evidence_comment_ids': []},
        {'n_distinct_timestamps': 1, 'evidence_comment_ids': ['c1', 'c2']},
    ]}
    with pytest.raises(AssertionError, match='Missing or insufficient evidence_comment_ids'):
        demo.assert_repeated_evidence(ai)


@pytest.mark.parametrize('ai, message', [
    ({}, 'Repeated harassment not detected'),
    ({'suspected_repeated_harassment': False}, 'Repeated harassment not detected'),
    ({'suspected_repeated_harassment': True}, 'No repeated harassment evidence'),
    ({'suspected_repeated_harassment': True, 'evidence': [
        {'evidence_comment_ids': ['c1', 'c2']}
    ]}, 'No repeated harassment evidence'),
])
def test_demo_rejects_missing_detection_or_repeated_timestamps(ai, message):
    with pytest.raises(AssertionError, match=message):
        demo.assert_repeated_evidence(ai)


def test_demo_accepts_two_distinct_ids_with_repeated_timestamps():
    demo.assert_repeated_evidence({
        'suspected_repeated_harassment': True,
        'evidence': [{'n_distinct_timestamps': 2,
                      'evidence_comment_ids': ['c1', 'c2']}],
    })
