import pytest
from cs329z_hw1.pipelines.priority import parse_reply




@pytest.mark.parametrize(
        "reply, expected_category",
        [
            ('{"reason": "deadline today", "category": "urgent"}', "urgent"),
            ("not json at all", "unknown"),
            ("", "unknown"),
            ('{"reason": "deadline today", "category": "high"}', "unknown"),
            ('{"reason": "deadline today", "category": 1}', "unknown"),
            ('{"reason": "deadline today", "category": "1"}', "unknown"),
        ])
def test_category(reply, expected_category):
    result = parse_reply(reply)
    assert result["category"] == expected_category
    