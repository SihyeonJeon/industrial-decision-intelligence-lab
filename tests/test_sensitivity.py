from __future__ import annotations

import pytest

from decision_lab.sensitivity import parse_float_list


def test_parse_float_list_rejects_invalid_cost_values() -> None:
    for raw in ("", "0.01,0", "-1,2", "nan,1", "inf,1"):
        with pytest.raises(ValueError):
            parse_float_list(raw, "cost grid")


def test_parse_float_list_sorts_and_deduplicates() -> None:
    assert parse_float_list("4,2,4", "cost grid") == [2.0, 4.0]
