import json
import random
import re
import time

import pytest
from cs329z_hw1.pipelines.digest import is_better, classify_all

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


def slow_lm(messages):
    time.sleep(0.2)
    return '{"reason": "r", "category": "normal"}'

def make_email(n: int) -> dict:
    return {
        "id": f"em-9{n:04d}",
        "thread_id": f"th-9{n:04d}",
        "reply_to": None,
        "from": f"person{n}@cardinal.example",
        "to": ["sam.lee@cardinal.example"],
        "date": f"2001-05-14T{8 + n:02d}:00:00Z",   # n <= 15, otherwise the hour goes past 23
        "subject": f"email-{n:02d}",                 # unique marker: email-01 is not a substring of email-10
        "body": "test body",
    }

def test_classify_all_is_concurrent():
    emails = [make_email(n) for n in range(10)]
    start = time.perf_counter()
    pairs = classify_all(emails, slow_lm)
    elapsed = time.perf_counter() - start

    assert len(pairs) == len(emails)
    # Sequential: 10 x 0.2 = 2.0s. With 4 workers: 3 rounds x 0.2 = 0.6s.
    # Use 1.2s to leave margin for a slow machine.
    assert elapsed < 1.2, f"took {elapsed:.2f}s; classify_all looks sequential"


def random_lm(messages):
    """Sleeps for a random time, so later emails may finish first.
    Even-numbered emails are urgent, odd-numbered ones are normal."""
    time.sleep(random.uniform(0, 0.1))
    n = int(re.search(r"email-(\d{2})", messages[-1]["content"]).group(1))
    category = "urgent" if n % 2 == 0 else "normal"
    return json.dumps({"reason": "r", "category": category})

def test_classify_all_keeps_order():
    emails = [make_email(n) for n in range(10)]
    pairs = classify_all(emails, random_lm)

    assert [e["id"] for e, _ in pairs] == [e["id"] for e in emails]
    for n, (_, cls) in enumerate(pairs):
        expected = "urgent" if n % 2 == 0 else "normal"
        assert cls["category"] == expected, f"email {n} was paired with the wrong result"


