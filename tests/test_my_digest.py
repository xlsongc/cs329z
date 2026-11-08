import pytest
from cs329z_hw1.pipelines.digest import is_better

def make(category, date):
    email = {"id": "x", "thread_id": "t1", "date": date}
    return (email, {"category": category, "reason": "r"})

def test_urgent_beats_normal():
    assert is_better(make("urgent", "2001-06-01T09:00:00Z"),
                     make("normal", "2001-06-01T09:00:00Z"))

def test_urgent_beats_unknown():
    assert is_better(make("urgent", "2001-06-01T09:00:00Z"),
                     make("unknown", "2001-06-01T09:00:00Z"))

def test_latest_beats_earlier():
    assert is_better(make("urgent", "2001-06-01T09:00:00Z"),
                     make("urgent", "2001-05-01T09:00:00Z"))

def test_latest_beats_earlier_normal_unknown():
    assert is_better(make("unknown", "2001-06-01T17:00:00Z"),
                     make("normal", "2001-06-01T16:00:00Z"))

