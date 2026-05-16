"Unit tests for Vector2d utility."
import pytest
from tribes.utils.vector2d import Vector2d


def test_chebychev_distance_same_point():
    p = Vector2d(3, 4)
    assert Vector2d.chebychev_distance(p, p) == 0


def test_chebychev_distance_horizontal():
    assert Vector2d.chebychev_distance(Vector2d(0, 0), Vector2d(5, 0)) == 5


def test_chebychev_distance_diagonal():
    assert Vector2d.chebychev_distance(Vector2d(0, 0), Vector2d(3, 4)) == 4


def test_neighborhood_radius_1():
    center = Vector2d(5, 5)
    neighbors = list(center.neighborhood(1, 0, 11))
    # Should contain the 8 surrounding tiles (not center itself in Java impl)
    # Verify each neighbor is within Chebyshev distance 1
    for n in neighbors:
        assert Vector2d.chebychev_distance(center, n) <= 1
    # All neighbors should be unique
    coords = [(n.x, n.y) for n in neighbors]
    assert len(coords) == len(set(coords))


def test_neighborhood_edge_clamps():
    corner = Vector2d(0, 0)
    neighbors = list(corner.neighborhood(1, 0, 10))
    for n in neighbors:
        assert 0 <= n.x < 10
        assert 0 <= n.y < 10


def test_equality():
    assert Vector2d(2, 3) == Vector2d(2, 3)
    assert Vector2d(1, 2) != Vector2d(2, 1)


def test_dist():
    assert Vector2d(0, 0).dist(3, 4) == pytest.approx(5.0)
