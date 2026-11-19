import pytest

from cs329z_hw1.pipelines.email_qa import parse_reply


def answer(text, support=None):
    return {"action": "answer", "answer": text, "support": support or []}


def search(query):
    return {"action": "search", "query": query}


@pytest.mark.parametrize("reply, expected", [
    # normal answer
    ('{"answer": "Room 101", "support": ["em-1"]}', answer("Room 101", ["em-1"])),
    # the model says there is no answer
    ('{"answer": null}', answer(None)),
    ('{"answer": "   "}', answer(None)),
    ('{"answer": ["a"]}', answer(None)),
    # wrong types are repaired
    ('{"answer": 42, "support": "em-1"}', answer("42")),
    ('{"answer": "x", "support": ["em-1", 7, null]}', answer("x", ["em-1"])),
    # normal search
    ('{"search": " X hotel "}', search("X hotel")),
    ('{"search": 42}', search("42")),
    ('```json\n{"search": "X hotel"}\n```', search("X hotel")),
    # answer wins over search
    ('{"answer": "A", "search": "B"}', answer("A")),
    # parse failures
    ('{"search": "  "}', None),
    ("%%% <<>> lorem ipsum {]", None),
    ("", None),
    ("{}", None),
    ("[1, 2]", None),
    # the scripted replies from tests/test_email_qa.py that are not JSON
    ("SEARCH: budget review room", None),
    ("<search>budget review room</search>", None),
    ('{"action": "search", "query": "budget review room"}', None),
])
def test_parse_reply(reply, expected):
    assert parse_reply(reply) == expected
