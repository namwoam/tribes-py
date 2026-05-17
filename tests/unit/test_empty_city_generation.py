"Unit tests for empty-city (village) placement in procedurally generated levels."

import random

from tribes.types import GAME_MODE, TERRAIN, TRIBE as TRIBE_TYPE
from tribes.game.game_state import GameState


def _make_gs(tribes_enum, seed=42):
    rnd = random.Random(seed)
    gs = GameState(rnd, GAME_MODE.SCORE)
    gs.init_generated(seed, tribes_enum)
    return gs


def _count_terrain(gs, terrain):
    board = gs.get_board()
    size = board.get_size()
    return sum(
        1
        for x in range(size)
        for y in range(size)
        if board.get_terrain_at(x, y) is terrain
    )


def _get_village_positions(gs):
    board = gs.get_board()
    size = board.get_size()
    return [
        (x, y)
        for x in range(size)
        for y in range(size)
        if board.get_terrain_at(x, y) is TERRAIN.VILLAGE
    ]


# ------------------------------------------------------------------
# Helper: _generated_empty_city_positions
# ------------------------------------------------------------------


def _empty_city_positions(num_tribes, seed=42):
    gs = GameState(random.Random(seed), GAME_MODE.SCORE)
    size = max(11, num_tribes * 4)
    city_positions = gs._generated_city_positions(size, num_tribes)
    occupied = set(city_positions)
    rnd = random.Random(seed)
    return gs._generated_empty_city_positions(size, occupied, rnd)


class TestEmptyCityCount:
    def test_at_least_one_empty_city_for_2_tribes(self):
        positions = _empty_city_positions(2)
        assert len(positions) >= 1

    def test_at_least_one_empty_city_for_4_tribes(self):
        positions = _empty_city_positions(4)
        assert len(positions) >= 1

    def test_count_scales_with_map_size(self):
        # size = max(11, n*4); expected = max(1, size//4)
        for num_tribes in (2, 4, 6, 8):
            size = max(11, num_tribes * 4)
            expected = max(1, size // 4)
            positions = _empty_city_positions(num_tribes)
            msg = (
                f"num_tribes={num_tribes}: expected {expected}"
                f" empty cities, got {len(positions)}"
            )
            assert len(positions) == expected, msg

    def test_no_overlap_with_tribe_capitals(self):
        for num_tribes in (2, 4):
            gs = GameState(random.Random(42), GAME_MODE.SCORE)
            size = max(11, num_tribes * 4)
            city_positions = gs._generated_city_positions(size, num_tribes)
            occupied = set(city_positions)
            empty = gs._generated_empty_city_positions(
                size, occupied, random.Random(42)
            )
            overlap = set(empty) & occupied
            assert overlap == set(), f"Villages overlap tribe capitals: {overlap}"

    def test_no_duplicate_empty_city_positions(self):
        positions = _empty_city_positions(4)
        assert len(positions) == len(set(positions))

    def test_min_gap_between_empty_cities(self):
        positions = _empty_city_positions(4)
        for i, (x1, y1) in enumerate(positions):
            for j, (x2, y2) in enumerate(positions):
                if i != j:
                    dist = abs(x1 - x2) + abs(y1 - y2)
                    msg = (
                        f"Villages at {(x1, y1)} and"
                        f" {(x2, y2)} are too close (dist={dist})"
                    )
                    assert dist >= 3, msg

    def test_min_gap_from_tribe_capitals(self):
        num_tribes = 4
        gs = GameState(random.Random(42), GAME_MODE.SCORE)
        size = max(11, num_tribes * 4)
        city_positions = gs._generated_city_positions(size, num_tribes)
        occupied = set(city_positions)
        empty = gs._generated_empty_city_positions(size, occupied, random.Random(42))
        for vx, vy in empty:
            for cx, cy in city_positions:
                dist = abs(vx - cx) + abs(vy - cy)
                msg = (
                    f"Village at {(vx, vy)} too close"
                    f" to capital at {(cx, cy)} (dist={dist})"
                )
                assert dist >= 3, msg

    def test_all_positions_within_bounds(self):
        num_tribes = 4
        gs = GameState(random.Random(42), GAME_MODE.SCORE)
        size = max(11, num_tribes * 4)
        city_positions = gs._generated_city_positions(size, num_tribes)
        occupied = set(city_positions)
        empty = gs._generated_empty_city_positions(size, occupied, random.Random(42))
        for x, y in empty:
            assert (
                0 <= x < size and 0 <= y < size
            ), f"Village at {(x, y)} out of bounds for size={size}"


# ------------------------------------------------------------------
# Integration: villages appear on the generated board
# ------------------------------------------------------------------


class TestVillagesOnBoard:
    def test_2_tribes_board_has_villages(self):
        gs = _make_gs([TRIBE_TYPE.IMPERIUS, TRIBE_TYPE.BARDUR])
        assert _count_terrain(gs, TERRAIN.VILLAGE) >= 1

    def test_4_tribes_board_has_villages(self):
        gs = _make_gs(
            [
                TRIBE_TYPE.IMPERIUS,
                TRIBE_TYPE.BARDUR,
                TRIBE_TYPE.XIN_XI,
                TRIBE_TYPE.OUMAJI,
            ]
        )
        assert _count_terrain(gs, TERRAIN.VILLAGE) >= 1

    def test_village_count_matches_formula(self):
        tribes = [
            TRIBE_TYPE.IMPERIUS,
            TRIBE_TYPE.BARDUR,
            TRIBE_TYPE.XIN_XI,
            TRIBE_TYPE.OUMAJI,
        ]
        gs = _make_gs(tribes)
        size = gs.get_board().get_size()
        expected = max(1, size // 4)
        actual = _count_terrain(gs, TERRAIN.VILLAGE)
        assert actual == expected

    def test_villages_not_on_tribe_capital_positions(self):
        tribes = [TRIBE_TYPE.IMPERIUS, TRIBE_TYPE.BARDUR]
        gs = _make_gs(tribes)
        village_positions = set(_get_village_positions(gs))
        board = gs.get_board()
        # Tribe capital positions have CITY terrain
        size = board.get_size()
        capital_positions = {
            (x, y)
            for x in range(size)
            for y in range(size)
            if board.get_terrain_at(x, y) is TERRAIN.CITY
        }
        assert village_positions.isdisjoint(capital_positions)

    def test_different_seeds_produce_different_village_layouts(self):
        tribes = [TRIBE_TYPE.IMPERIUS, TRIBE_TYPE.BARDUR]
        positions_a = set(_get_village_positions(_make_gs(tribes, seed=1)))
        positions_b = set(_get_village_positions(_make_gs(tribes, seed=2)))
        # Very unlikely to be identical across seeds
        assert positions_a != positions_b
