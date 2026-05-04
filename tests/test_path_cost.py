"""Unit tests for tsdp.path_cost."""
import numpy as np
import pytest

from tsdp.config import PAPER_DEFAULT
from tsdp.path_cost import (
    edge_cost, astar, path_length_metres, mean_safety_distance,
)


class TestEdgeCost:
    def test_zero_distance(self):
        c = edge_cost((0, 0), (0, 0), risk_j=0.0,
                      is_no_fly_j=False, config=PAPER_DEFAULT)
        assert c == 0.0

    def test_no_fly_returns_sentinel(self):
        c = edge_cost((0, 0), (1, 0), risk_j=0.0,
                      is_no_fly_j=True, config=PAPER_DEFAULT)
        assert c == PAPER_DEFAULT.no_fly_sentinel

    def test_risk_amplifies_cost(self):
        c_low = edge_cost((0, 0), (1, 0), risk_j=0.0,
                          is_no_fly_j=False, config=PAPER_DEFAULT)
        c_high = edge_cost((0, 0), (1, 0), risk_j=1.0,
                           is_no_fly_j=False, config=PAPER_DEFAULT)
        assert c_high > c_low
        # With mu=5, risk=1.0 should give cost = 1 * (1 + 5*1) = 6
        assert c_high == pytest.approx(6.0)


class TestAstarSimple:
    """Trivial chain graph 0-1-2-3."""

    @pytest.fixture
    def chain(self):
        centroids = np.array([[0, 0], [1, 0], [2, 0], [3, 0]], dtype=float)
        adjacency = {0: [1], 1: [0, 2], 2: [1, 3], 3: [2]}
        risks = np.zeros(4)
        no_fly = np.zeros(4, dtype=bool)
        return centroids, adjacency, risks, no_fly

    def test_finds_path(self, chain):
        centroids, adj, risks, no_fly = chain
        path, n_expanded = astar(centroids, adj, risks, no_fly,
                                 start_idx=0, goal_idx=3,
                                 config=PAPER_DEFAULT)
        assert path == [0, 1, 2, 3]
        assert n_expanded > 0

    def test_no_path_when_goal_unreachable(self, chain):
        centroids, adj, risks, no_fly = chain
        no_fly[2] = True  # block the chain
        adj_no_2 = {0: [1], 1: [0], 2: [], 3: []}
        path, _ = astar(centroids, adj_no_2, risks, no_fly,
                        start_idx=0, goal_idx=3,
                        config=PAPER_DEFAULT)
        assert path is None

    def test_start_equals_goal(self, chain):
        centroids, adj, risks, no_fly = chain
        path, n_expanded = astar(centroids, adj, risks, no_fly,
                                 start_idx=2, goal_idx=2,
                                 config=PAPER_DEFAULT)
        assert path == [2]
        assert n_expanded == 0


class TestPathMetrics:
    def test_path_length_zero_for_single_node(self):
        centroids = np.array([[0, 0]])
        assert path_length_metres(centroids, [0]) == 0.0

    def test_path_length_simple(self):
        centroids = np.array([[0, 0], [3, 0], [3, 4]])
        # 0 -> 1: 3, 1 -> 2: 4, total 7
        assert path_length_metres(centroids, [0, 1, 2]) == pytest.approx(7.0)

    def test_mean_safety_distance(self):
        centroids = np.array([[0, 0], [10, 0]])
        obstacles = np.array([[0, 5]])
        # path point 0 dist=5, path point 1 dist=sqrt(125) ~= 11.18
        # mean ~= 8.09
        result = mean_safety_distance(centroids, [0, 1], obstacles)
        assert result == pytest.approx((5.0 + np.sqrt(125)) / 2.0, rel=1e-6)
