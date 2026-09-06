"""Repository-wide pytest governance hooks.

One hash-frozen pre-execution test remains part of scientific provenance after
the governed v3 execution closed. It is retained byte-for-byte and reported as
an expected historical condition; current-state coverage lives separately.
"""

from __future__ import annotations

import pytest


HISTORICAL_PREEXECUTION_NODE = (
    "tests/test_defensive_coverage_redistribution_v3_governance.py::"
    "test_v2_invalid_closure_exists_without_protected_results_and_v3_is_unexecuted"
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if item.nodeid == HISTORICAL_PREEXECUTION_NODE:
            item.add_marker(pytest.mark.xfail(
                reason=(
                    "hash-frozen pre-execution assertion retained for provenance; "
                    "the governed v3 result is now closed and covered by current-state tests"
                ),
                run=False,
                strict=True,
            ))
