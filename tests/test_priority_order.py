"""Unit tests for evaluator priority order logic."""

import pytest
from src.evaluator import (
    _score,
    _get_criterion_value,
    select_best,
    DEFAULT_PRIORITY_ORDER,
    PRIORITY_CRITERIA,
)
from src.app import reorder_priority
from src.algorithms.base import SearchResult


# --- Test Fixtures ---

@pytest.fixture
def mock_results():
    """Create mock SearchResult objects with varied metrics."""
    return [
        SearchResult(
            name="AlgoA",
            path=[(0, 0), (1, 1)],
            cost=10.0,
            explored_nodes=50,
            duration=0.1,
            success=True,
            visited_order=[(0, 0), (1, 1)],
        ),
        SearchResult(
            name="AlgoB",
            path=[(0, 0), (1, 0), (1, 1)],
            cost=8.0,
            explored_nodes=100,
            duration=0.2,
            success=True,
            visited_order=[(0, 0), (1, 0), (1, 1)],
        ),
        SearchResult(
            name="AlgoC",
            path=[(0, 0), (0, 1), (1, 1)],
            cost=12.0,
            explored_nodes=30,
            duration=0.05,
            success=True,
            visited_order=[(0, 0), (0, 1), (1, 1)],
        ),
        SearchResult(
            name="AlgoD_failed",
            path=[],
            cost=float("inf"),
            explored_nodes=0,
            duration=0.0,
            success=False,
            visited_order=[],
        ),
    ]


# --- Tests for _get_criterion_value ---

class TestGetCriterionValue:
    def test_cost_criterion(self, mock_results):
        result = mock_results[0]  # AlgoA: cost=10.0
        assert _get_criterion_value(result, "cost") == 10.0

    def test_nodes_criterion(self, mock_results):
        result = mock_results[0]  # AlgoA: nodes=50
        assert _get_criterion_value(result, "nodes") == 50.0

    def test_time_criterion(self, mock_results):
        result = mock_results[0]  # AlgoA: duration=0.1
        assert _get_criterion_value(result, "time") == 0.1

    def test_unknown_criterion_raises(self, mock_results):
        with pytest.raises(ValueError, match="Unknown criterion"):
            _get_criterion_value(mock_results[0], "invalid")


# --- Tests for _score ---

class TestScore:
    def test_default_priority_order(self, mock_results):
        """Default order is (cost, nodes, time)."""
        result = mock_results[0]  # cost=10, nodes=50, time=0.1
        score = _score(result)
        assert score == (10.0, 50.0, 0.1)

    def test_custom_priority_order_time_first(self, mock_results):
        """Test with time as primary priority."""
        result = mock_results[0]  # cost=10, nodes=50, time=0.1
        score = _score(result, ("time", "cost", "nodes"))
        assert score == (0.1, 10.0, 50.0)

    def test_custom_priority_order_nodes_first(self, mock_results):
        """Test with nodes as primary priority."""
        result = mock_results[1]  # cost=8, nodes=100, time=0.2
        score = _score(result, ("nodes", "time", "cost"))
        assert score == (100.0, 0.2, 8.0)


# --- Tests for select_best ---

class TestSelectBest:
    def test_default_order_selects_lowest_cost(self, mock_results):
        """Default order (cost first) should select AlgoB with cost=8."""
        best = select_best(mock_results)
        assert best is not None
        assert best.name == "AlgoB"
        assert best.cost == 8.0

    def test_nodes_first_selects_least_explored(self, mock_results):
        """With nodes first, should select AlgoC with 30 nodes."""
        best = select_best(mock_results, ("nodes", "cost", "time"))
        assert best is not None
        assert best.name == "AlgoC"
        assert best.explored_nodes == 30

    def test_time_first_selects_fastest(self, mock_results):
        """With time first, should select AlgoC with 0.05s."""
        best = select_best(mock_results, ("time", "nodes", "cost"))
        assert best is not None
        assert best.name == "AlgoC"
        assert best.duration == 0.05

    def test_failed_results_excluded(self, mock_results):
        """Failed results should never be selected as best."""
        # Only include the failed result
        failed_only = [mock_results[3]]
        best = select_best(failed_only)
        assert best is None

    def test_tie_breaking_by_secondary_criterion(self):
        """When primary criterion ties, secondary should break it."""
        tied_results = [
            SearchResult(
                name="TieA",
                path=[],
                cost=10.0,
                explored_nodes=50,
                duration=0.1,
                success=True,
                visited_order=[],
            ),
            SearchResult(
                name="TieB",
                path=[],
                cost=10.0,  # Same cost
                explored_nodes=30,  # Fewer nodes
                duration=0.2,
                success=True,
                visited_order=[],
            ),
        ]
        # With default (cost, nodes, time), TieB wins due to fewer nodes
        best = select_best(tied_results, ("cost", "nodes", "time"))
        assert best is not None
        assert best.name == "TieB"

    def test_empty_results_returns_none(self):
        """Empty results list should return None."""
        best = select_best([])
        assert best is None


# --- Tests for current behavior match ---

class TestDefaultBehaviorMatch:
    """Verify the new implementation matches the previous fixed behavior."""

    def test_default_constants_defined(self):
        """Verify the default constants are correctly defined."""
        assert PRIORITY_CRITERIA == ("cost", "nodes", "time")
        assert DEFAULT_PRIORITY_ORDER == ("cost", "nodes", "time")

    def test_default_priority_matches_original_score(self, mock_results):
        """Default priority should produce same ranking as original implementation.
        
        Original: _score = (result.cost, result.explored_nodes, result.duration)
        """
        for result in mock_results:
            if not result.success:
                continue
            new_score = _score(result, DEFAULT_PRIORITY_ORDER)
            expected = (result.cost, float(result.explored_nodes), result.duration)
            assert new_score == expected


class TestRankOrderUtility:
    """Ensure the drag-and-drop order helper behaves as expected."""

    def test_reorder_priority_moves_last_to_first(self):
        start = list(DEFAULT_PRIORITY_ORDER)
        updated = reorder_priority(start, 2, 0)
        assert updated == ["time", "cost", "nodes"]
        assert start == list(DEFAULT_PRIORITY_ORDER), "Original list should remain unchanged."

    def test_reorder_priority_swaps_middle(self):
        start = list(DEFAULT_PRIORITY_ORDER)
        updated = reorder_priority(start, 2, 1)
        assert updated == ["cost", "time", "nodes"]

    def test_score_respects_reordered_priority(self, mock_results):
        order = reorder_priority(list(DEFAULT_PRIORITY_ORDER), 2, 0)
        result = mock_results[0]  # AlgoA: cost=10, nodes=50, time=0.1
        score = _score(result, tuple(order))
        assert score == (0.1, 10.0, 50.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
