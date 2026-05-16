"Unit tests for TribeResult ordering."
import pytest
from tribes.game.tribe_result import TribeResult
from tribes.types import RESULT


def _tr(id_: int, result: RESULT = RESULT.INCOMPLETE, score: int = 100,
        techs: int = 5, cities: int = 3, prod: int = 10,
        wars: int = 0, stars: int = 0) -> TribeResult:
    return TribeResult(id_, result, score, techs, cities, prod, wars, stars)


def test_win_beats_loss():
    winner = _tr(0, RESULT.WIN)
    loser = _tr(1, RESULT.LOSS)
    assert winner < loser


def test_higher_score_ranks_first():
    high = _tr(0, score=500)
    low = _tr(1, score=100)
    assert high < low


def test_more_techs_breaks_score_tie():
    a = _tr(0, score=200, techs=10)
    b = _tr(1, score=200, techs=5)
    assert a < b


def test_copy_preserves_fields():
    tr = TribeResult(7, RESULT.WIN, 999, 15, 8, 50, 3, 12)
    c = tr.copy()
    assert c.id == 7
    assert c.result is RESULT.WIN
    assert c.score == 999
    assert c.num_techs_researched == 15
    assert c.num_cities == 8
    assert c.production == 50
    assert c.num_wars == 3
    assert c.num_stars == 12


def test_sorting():
    results = [
        _tr(2, RESULT.LOSS, score=50),
        _tr(0, RESULT.WIN, score=10),
        _tr(1, RESULT.INCOMPLETE, score=200),
    ]
    results.sort()
    assert results[0].id == 0   # WIN always first
    assert results[1].id == 1   # higher score next
    assert results[2].id == 2
