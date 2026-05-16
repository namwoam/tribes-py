"Unit tests for types.py enums."

from tribes.types import ACTION, GAME_MODE, RESULT, TERRAIN, TRIBE, TECHNOLOGY, UNIT


def test_action_enum_all_unique():
    """No two ACTION members should be aliases (same identity) of each other."""
    members = list(ACTION)
    for i, a in enumerate(members):
        for b in members[i + 1 :]:
            assert a is not b, f"{a.name} and {b.name} are aliases"


def test_action_end_turn_distinct_from_build():
    assert ACTION.END_TURN is not ACTION.BUILD
    assert ACTION.SPAWN is not ACTION.BUILD
    assert ACTION.LEVEL_UP is not ACTION.BUILD
    assert ACTION.RESOURCE_GATHERING is not ACTION.BUILD
    assert ACTION.RESEARCH_TECH is not ACTION.BUILD
    assert ACTION.SEND_STARS is not ACTION.BUILD
    assert ACTION.DECLARE_WAR is not ACTION.BUILD
    assert ACTION.MAKE_VETERAN is not ACTION.BUILD
    assert ACTION.RECOVER is not ACTION.BUILD


def test_action_tech_requirement():
    assert ACTION.BURN_FOREST.get_technology_requirement() is TECHNOLOGY.CHIVALRY
    assert ACTION.BUILD.get_technology_requirement() is None
    assert ACTION.DISBAND.get_technology_requirement() is TECHNOLOGY.FREE_SPIRIT


def test_game_mode_max_turns():
    from tribes import constants as C

    assert GAME_MODE.CAPITALS.get_max_turns() == C.MAX_TURNS_CAPITALS
    assert GAME_MODE.SCORE.get_max_turns() == C.MAX_TURNS


def test_terrain_chars():
    assert TERRAIN.get_type(".") is TERRAIN.PLAIN
    assert TERRAIN.get_type("f") is TERRAIN.FOREST
    assert TERRAIN.get_type("m") is TERRAIN.MOUNTAIN
    assert TERRAIN.get_type("c") is TERRAIN.CITY
    assert TERRAIN.get_type("X") is None


def test_tribe_colors():
    for t in TRIBE:
        c = t.get_color()
        assert len(c) == 3
        assert all(0 <= v <= 255 for v in c)


def test_unit_is_ranged():
    assert UNIT.ARCHER.is_ranged()
    assert UNIT.CATAPULT.is_ranged()
    assert not UNIT.WARRIOR.is_ranged()
    assert not UNIT.SWORDMAN.is_ranged()


def test_result_enum():
    assert RESULT.WIN is not RESULT.LOSS
    assert RESULT.INCOMPLETE is not RESULT.WIN
