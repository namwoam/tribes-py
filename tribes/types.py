"All game enums ported from Types.java."
from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# TECHNOLOGY
# ---------------------------------------------------------------------------

class TECHNOLOGY(Enum):
    CLIMBING       = (1, None)
    FISHING        = (1, None)
    HUNTING        = (1, None)
    ORGANIZATION   = (1, None)
    RIDING         = (1, None)
    ARCHERY        = (2, "HUNTING")
    FARMING        = (2, "ORGANIZATION")
    FORESTRY       = (2, "HUNTING")
    FREE_SPIRIT    = (2, "RIDING")
    MEDITATION     = (2, "CLIMBING")
    MINING         = (2, "CLIMBING")
    ROADS          = (2, "RIDING")
    SAILING        = (2, "FISHING")
    SHIELDS        = (2, "ORGANIZATION")
    WHALING        = (2, "FISHING")
    AQUATISM       = (3, "WHALING")
    CHIVALRY       = (3, "FREE_SPIRIT")
    CONSTRUCTION   = (3, "FARMING")
    MATHEMATICS    = (3, "FORESTRY")
    NAVIGATION     = (3, "SAILING")
    SMITHERY       = (3, "MINING")
    SPIRITUALISM   = (3, "ARCHERY")
    TRADE          = (3, "ROADS")
    PHILOSOPHY     = (3, "MEDITATION")

    def __init__(self, tier: int, parent_name: Optional[str]) -> None:
        self._tier = tier
        self._parent_name = parent_name
        self._children: Optional[list[TECHNOLOGY]] = None

    def get_parent_tech(self) -> Optional[TECHNOLOGY]:
        if self._parent_name is None:
            return None
        return TECHNOLOGY[self._parent_name]

    def get_child_tech(self) -> list[TECHNOLOGY]:
        if self._children is None:
            self._children = [t for t in TECHNOLOGY if t.get_parent_tech() is self]
        return self._children

    def get_cost(self, num_of_cities: int, tt: "TechnologyTree") -> int:
        from tribes.config import TECH_BASE_COST, TECH_DISCOUNT_VALUE
        cost = TECH_BASE_COST + self._tier * num_of_cities
        if tt.is_researched(TECHNOLOGY.PHILOSOPHY):
            cost = int(cost * TECH_DISCOUNT_VALUE)
        return cost

    def get_points(self) -> int:
        from tribes.config import TECH_TIER_POINTS
        return self._tier * TECH_TIER_POINTS

    def get_tier(self) -> int:
        return self._tier


# ---------------------------------------------------------------------------
# TRIBE
# ---------------------------------------------------------------------------

class TRIBE(Enum):
    XIN_XI   = (0,  "Xin-Xi",   "CLIMBING",     "WARRIOR",
                (251, 2, 7),    (253, 130, 123), (174, 66, 48))
    IMPERIUS = (1,  "Imperius", "ORGANIZATION", "WARRIOR",
                (0, 0, 255),    (102, 125, 255), (50, 73, 177))
    BARDUR   = (2,  "Bardur",   "HUNTING",      "WARRIOR",
                (76, 76, 76),   (176, 178, 178), (70, 58, 58))
    OUMAJI   = (3,  "Oumaji",   "RIDING",       "RIDER",
                (255, 255, 10), (242, 255, 100), (146, 144, 0))
    KICKOO   = (4,  "Kickoo",   "FISHING",      "WARRIOR",
                (0, 255, 0),    (82, 245, 82),   (0, 145, 0))
    HOODRICK = (5,  "Hoodrick", "ARCHERY",      "ARCHER",
                (153, 102, 0),  (199, 137, 13),  (102, 69, 0))
    LUXIDOOR = (6,  "Luxidoor", None,            "WARRIOR",
                (171, 59, 214), (191, 81, 234),  (116, 41, 145))
    VENGIR   = (7,  "Vengir",   "SMITHERY",     "SWORDMAN",
                (255, 255, 255),(220, 220, 220),  (145, 145, 145))
    ZEBASI   = (8,  "Zebasi",   "FARMING",      "WARRIOR",
                (255, 153, 0),  (255, 171, 47),  (145, 87, 0))
    AI_MO    = (9,  "Ai-Mo",    "MEDITATION",   "WARRIOR",
                (54, 226, 170), (168, 255, 229), (35, 145, 109))
    QUETZALI = (10, "Quetzali", "SHIELDS",      "DEFENDER",
                (39, 92, 74),   (79, 165, 136),  (20, 51, 41))
    YADAKK   = (11, "Yadakk",   "ROADS",        "WARRIOR",
                (125, 38, 28),  (177, 70, 57),   (92, 33, 13))

    def __init__(self, key: int, name: str, initial_tech_name: Optional[str],
                 starting_unit_name: str,
                 color: tuple, color_light: tuple, color_dark: tuple) -> None:
        self._key = key
        self._name = name
        self._initial_tech_name = initial_tech_name
        self._starting_unit_name = starting_unit_name
        self._color = color
        self._color_light = color_light
        self._color_dark = color_dark

    @staticmethod
    def get_type_by_key(key: int) -> Optional[TRIBE]:
        for t in TRIBE:
            if t._key == key:
                return t
        return None

    def get_key(self) -> int:
        return self._key

    def get_name(self) -> str:
        return self._name

    def get_initial_tech(self) -> Optional[TECHNOLOGY]:
        if self._initial_tech_name is None:
            return None
        return TECHNOLOGY[self._initial_tech_name]

    def get_starting_unit(self) -> "UNIT":
        return UNIT[self._starting_unit_name]

    def get_color(self) -> tuple:
        return self._color

    def get_color_light(self) -> tuple:
        return self._color_light

    def get_color_dark(self) -> tuple:
        return self._color_dark


# ---------------------------------------------------------------------------
# TURN_STATUS
# ---------------------------------------------------------------------------

class TURN_STATUS(Enum):
    FRESH             = "FRESH"
    MOVED             = "MOVED"
    ATTACKED          = "ATTACKED"
    MOVED_AND_ATTACKED = "MOVED_AND_ATTACKED"
    PUSHED            = "PUSHED"
    FINISHED          = "FINISHED"


# ---------------------------------------------------------------------------
# TERRAIN
# ---------------------------------------------------------------------------

class TERRAIN(Enum):
    PLAIN         = (0, "img/terrain/plain.png",     '.')
    SHALLOW_WATER = (1, "img/terrain/water.png",     's')
    DEEP_WATER    = (2, "img/terrain/deepwater.png", 'd')
    MOUNTAIN      = (3, "img/terrain/mountain3.png", 'm')
    VILLAGE       = (4, "img/terrain/village2.png",  'v')
    CITY          = (5, "img/terrain/city3.png",     'c')
    FOREST        = (6, "img/terrain/forest2.png",   'f')
    FOG           = (7, "img/fog.png",               ' ')

    def __init__(self, key: int, image_file: str, map_char: str) -> None:
        self._key = key
        self._image_file = image_file
        self._map_char = map_char

    @staticmethod
    def get_type(terrain_char: str) -> Optional[TERRAIN]:
        for t in TERRAIN:
            if t._map_char == terrain_char:
                return t
        return None

    @staticmethod
    def get_type_by_key(key: int) -> Optional[TERRAIN]:
        for t in TERRAIN:
            if t._key == key:
                return t
        return None

    def get_key(self) -> int:
        return self._key

    def get_map_char(self) -> str:
        return self._map_char

    def is_water(self) -> bool:
        return self in (TERRAIN.SHALLOW_WATER, TERRAIN.DEEP_WATER)

    @staticmethod
    def board_equals(board1: list, board2: list) -> bool:
        if len(board1) != len(board2) or len(board1[0]) != len(board2[0]):
            return False
        for i in range(len(board1)):
            for j in range(len(board1[i])):
                b1 = board1[i][j]
                b2 = board2[i][j]
                if b1 is not None and b2 is not None and b1 != b2:
                    return False
        return True


# ---------------------------------------------------------------------------
# RESOURCE
# ---------------------------------------------------------------------------

class RESOURCE(Enum):
    FISH   = (0, "img/resource/fish2.png",   None,                     'h', 2,  1,  "FISHING")
    FRUIT  = (1, "img/resource/fruit2.png",  None,                     'f', 2,  1,  "ORGANIZATION")
    ANIMAL = (2, "img/resource/animal2.png", None,                     'a', 2,  1,  "HUNTING")
    WHALES = (3, "img/resource/whale2.png",  "img/resource/whale3.png",'w', 0,  10, "WHALING")
    ORE    = (5, "img/resource/ore2.png",    None,                     'o', 0,  0,  "MINING")
    CROPS  = (6, "img/resource/crops2.png",  None,                     'c', 0,  0,  "FARMING")
    RUINS  = (7, "img/resource/ruins2.png",  None,                     'r', 0,  0,  None)

    def __init__(self, key: int, image_file: str, secondary_image_file: Optional[str],
                 map_char: str, cost: int, bonus: int, tech_name: Optional[str]) -> None:
        self._key = key
        self._image_file = image_file
        self._secondary_image_file = secondary_image_file
        self._map_char = map_char
        self._cost = cost
        self._bonus = bonus
        self._tech_name = tech_name

    @staticmethod
    def get_type(resource_char: str) -> Optional[RESOURCE]:
        for r in RESOURCE:
            if r._map_char == resource_char:
                return r
        return None

    @staticmethod
    def get_type_by_key(key: int) -> Optional[RESOURCE]:
        for r in RESOURCE:
            if r._key == key:
                return r
        return None

    def get_key(self) -> int:
        return self._key

    def get_cost(self) -> int:
        return self._cost

    def get_bonus(self) -> int:
        return self._bonus

    def get_map_char(self) -> str:
        return self._map_char

    def get_technology_requirement(self) -> Optional[TECHNOLOGY]:
        if self._tech_name is None:
            return None
        return TECHNOLOGY[self._tech_name]


# ---------------------------------------------------------------------------
# BUILDING
# ---------------------------------------------------------------------------

class MONUMENT_STATUS(Enum):
    UNAVAILABLE = 0
    AVAILABLE   = 1
    BUILT       = 2

    def __init__(self, key: int) -> None:
        self._key = key

    def get_key(self) -> int:
        return self._key

    @staticmethod
    def get_type_by_key(key: int) -> Optional[MONUMENT_STATUS]:
        for m in MONUMENT_STATUS:
            if m._key == key:
                return m
        return None


class BUILDING(Enum):
    PORT            = (0,  "img/building/dock2.png",         None,              {"SHALLOW_WATER"})
    MINE            = (1,  "img/building/mine2.png",         "MINING",          {"MOUNTAIN"})
    FORGE           = (2,  "img/building/forge2.png",        "SMITHERY",        {"PLAIN"})
    FARM            = (3,  "img/building/farm2.png",         "FARMING",         {"PLAIN"})
    WINDMILL        = (4,  "img/building/windmill2.png",     "CONSTRUCTION",    {"PLAIN"})
    CUSTOMS_HOUSE   = (5,  "img/building/custom_house2.png", "TRADE",           {"PLAIN"})
    LUMBER_HUT      = (6,  "img/building/lumber_hut2.png",   "FORESTRY",        {"FOREST"})
    SAWMILL         = (7,  "img/building/sawmill2.png",      "MATHEMATICS",     {"PLAIN"})
    TEMPLE          = (8,  "img/building/temple2.png",       "FREE_SPIRIT",     {"PLAIN"})
    WATER_TEMPLE    = (9,  "img/building/temple2.png",       "AQUATISM",        {"SHALLOW_WATER", "DEEP_WATER"})
    FOREST_TEMPLE   = (10, "img/building/temple2.png",       "SPIRITUALISM",    {"FOREST"})
    MOUNTAIN_TEMPLE = (11, "img/building/temple2.png",       "MEDITATION",      {"MOUNTAIN"})
    ALTAR_OF_PEACE  = (12, "img/building/monument2.png",     "MEDITATION",      {"SHALLOW_WATER", "PLAIN"})
    EMPERORS_TOMB   = (13, "img/building/monument2.png",     "TRADE",           {"SHALLOW_WATER", "PLAIN"})
    EYE_OF_GOD      = (14, "img/building/monument2.png",     "NAVIGATION",      {"SHALLOW_WATER", "PLAIN"})
    GATE_OF_POWER   = (15, "img/building/monument2.png",     None,              {"SHALLOW_WATER", "PLAIN"})
    GRAND_BAZAR     = (16, "img/building/monument2.png",     "ROADS",           {"SHALLOW_WATER", "PLAIN"})
    PARK_OF_FORTUNE = (17, "img/building/monument2.png",     None,              {"SHALLOW_WATER", "PLAIN"})
    TOWER_OF_WISDOM = (18, "img/building/monument2.png",     "PHILOSOPHY",      {"SHALLOW_WATER", "PLAIN"})

    def __init__(self, key: int, image_file: str,
                 tech_name: Optional[str],
                 terrain_names: set) -> None:
        self._key = key
        self._image_file = image_file
        self._tech_name = tech_name
        self._terrain_names = terrain_names
        # cost/bonus wired up after class definition via _set_costs
        self._cost: int = 0
        self._bonus: int = 0

    # --- class methods / static helpers ---

    @staticmethod
    def string_to_type(type_str: str) -> Optional[BUILDING]:
        try:
            return BUILDING[type_str]
        except KeyError:
            return None

    @staticmethod
    def get_type_by_key(key: int) -> Optional[BUILDING]:
        for b in BUILDING:
            if b._key == key:
                return b
        return None

    @staticmethod
    def init_monuments() -> dict:
        return {
            BUILDING.ALTAR_OF_PEACE:  MONUMENT_STATUS.UNAVAILABLE,
            BUILDING.EMPERORS_TOMB:   MONUMENT_STATUS.UNAVAILABLE,
            BUILDING.EYE_OF_GOD:      MONUMENT_STATUS.UNAVAILABLE,
            BUILDING.GATE_OF_POWER:   MONUMENT_STATUS.UNAVAILABLE,
            BUILDING.PARK_OF_FORTUNE: MONUMENT_STATUS.UNAVAILABLE,
            BUILDING.TOWER_OF_WISDOM: MONUMENT_STATUS.UNAVAILABLE,
            BUILDING.GRAND_BAZAR:     MONUMENT_STATUS.UNAVAILABLE,
        }

    @staticmethod
    def init_monuments_from_dict(data: dict) -> dict:
        """data: {str(key): int(status_key)}"""
        result = {}
        for k, v in data.items():
            result[BUILDING.get_type_by_key(int(k))] = MONUMENT_STATUS.get_type_by_key(int(v))
        return result

    # --- instance helpers ---

    def get_key(self) -> int:
        return self._key

    def get_cost(self) -> int:
        return self._cost

    def get_bonus(self) -> int:
        return self._bonus

    def get_technology_requirement(self) -> Optional[TECHNOLOGY]:
        if self._tech_name is None:
            return None
        return TECHNOLOGY[self._tech_name]

    def get_terrain_requirements(self) -> set:
        return {TERRAIN[name] for name in self._terrain_names}

    def get_resource_constraint(self) -> Optional[RESOURCE]:
        if self is BUILDING.MINE:
            return RESOURCE.ORE
        if self is BUILDING.FARM:
            return RESOURCE.CROPS
        return None

    def get_adjacency_constraint(self) -> Optional[BUILDING]:
        if self is BUILDING.CUSTOMS_HOUSE:
            return BUILDING.PORT
        if self is BUILDING.WINDMILL:
            return BUILDING.FARM
        if self is BUILDING.FORGE:
            return BUILDING.MINE
        if self is BUILDING.SAWMILL:
            return BUILDING.LUMBER_HUT
        return None

    def get_matching_building(self) -> Optional[BUILDING]:
        mapping = {
            BUILDING.PORT:        BUILDING.CUSTOMS_HOUSE,
            BUILDING.FARM:        BUILDING.WINDMILL,
            BUILDING.MINE:        BUILDING.FORGE,
            BUILDING.LUMBER_HUT:  BUILDING.SAWMILL,
            BUILDING.CUSTOMS_HOUSE: BUILDING.PORT,
            BUILDING.WINDMILL:    BUILDING.FARM,
            BUILDING.FORGE:       BUILDING.MINE,
            BUILDING.SAWMILL:     BUILDING.LUMBER_HUT,
        }
        return mapping.get(self)

    def is_base(self) -> bool:
        return self in (BUILDING.FARM, BUILDING.MINE, BUILDING.LUMBER_HUT)

    def is_monument(self) -> bool:
        return self in (
            BUILDING.ALTAR_OF_PEACE, BUILDING.EMPERORS_TOMB, BUILDING.EYE_OF_GOD,
            BUILDING.GATE_OF_POWER, BUILDING.PARK_OF_FORTUNE, BUILDING.TOWER_OF_WISDOM,
            BUILDING.GRAND_BAZAR,
        )

    def is_temple(self) -> bool:
        return self in (
            BUILDING.TEMPLE, BUILDING.WATER_TEMPLE,
            BUILDING.MOUNTAIN_TEMPLE, BUILDING.FOREST_TEMPLE,
        )


def _wire_building_costs() -> None:
    """Inject cost/bonus values into BUILDING members from config constants."""
    from tribes import config as cfg
    _costs = {
        BUILDING.PORT:            (cfg.PORT_COST,         cfg.PORT_BONUS),
        BUILDING.MINE:            (cfg.MINE_COST,         cfg.MINE_BONUS),
        BUILDING.FORGE:           (cfg.FORGE_COST,        cfg.FORGE_BONUS),
        BUILDING.FARM:            (cfg.FARM_COST,         cfg.FARM_BONUS),
        BUILDING.WINDMILL:        (cfg.WIND_MILL_COST,    cfg.WIND_MILL_BONUS),
        BUILDING.CUSTOMS_HOUSE:   (cfg.CUSTOMS_COST,      cfg.CUSTOMS_BONUS),
        BUILDING.LUMBER_HUT:      (cfg.LUMBER_HUT_COST,   cfg.LUMBER_HUT_BONUS),
        BUILDING.SAWMILL:         (cfg.SAW_MILL_COST,     cfg.SAW_MILL_BONUS),
        BUILDING.TEMPLE:          (cfg.TEMPLE_COST,       cfg.TEMPLE_BONUS),
        BUILDING.WATER_TEMPLE:    (cfg.TEMPLE_COST,       cfg.TEMPLE_BONUS),
        BUILDING.FOREST_TEMPLE:   (cfg.TEMPLE_FOREST_COST,cfg.TEMPLE_BONUS),
        BUILDING.MOUNTAIN_TEMPLE: (cfg.TEMPLE_COST,       cfg.TEMPLE_BONUS),
        BUILDING.ALTAR_OF_PEACE:  (0,                     cfg.MONUMENT_BONUS),
        BUILDING.EMPERORS_TOMB:   (0,                     cfg.MONUMENT_BONUS),
        BUILDING.EYE_OF_GOD:      (0,                     cfg.MONUMENT_BONUS),
        BUILDING.GATE_OF_POWER:   (0,                     cfg.MONUMENT_BONUS),
        BUILDING.GRAND_BAZAR:     (0,                     cfg.MONUMENT_BONUS),
        BUILDING.PARK_OF_FORTUNE: (0,                     cfg.MONUMENT_BONUS),
        BUILDING.TOWER_OF_WISDOM: (0,                     cfg.MONUMENT_BONUS),
    }
    for member, (cost, bonus) in _costs.items():
        member._cost = cost
        member._bonus = bonus


# ---------------------------------------------------------------------------
# EXAMINE_BONUS
# ---------------------------------------------------------------------------

class EXAMINE_BONUS(Enum):
    SUPERUNIT   = (0, 0)
    RESEARCH    = (1, 0)
    POP_GROWTH  = (2, 3)
    EXPLORER    = (3, 0)
    RESOURCES   = (4, 10)

    def __init__(self, key: int, bonus: int) -> None:
        self._key = key
        self._bonus = bonus

    def get_bonus(self) -> int:
        return self._bonus

    @staticmethod
    def random(rng: "random.Random") -> EXAMINE_BONUS:
        import random as _random
        bonuses = list(EXAMINE_BONUS)
        return _random.choice(bonuses) if rng is None else bonuses[rng.randint(0, len(bonuses) - 1)]


# ---------------------------------------------------------------------------
# CITY_LEVEL_UP
# ---------------------------------------------------------------------------

class CITY_LEVEL_UP(Enum):
    WORKSHOP    = 2
    EXPLORER    = 2
    CITY_WALL   = 3
    RESOURCES   = 3
    POP_GROWTH  = 4
    BORDER_GROWTH = 4
    PARK        = 5
    SUPERUNIT   = 5

    def __init__(self, level: int) -> None:
        self._level = level

    def get_level(self) -> int:
        return self._level

    @staticmethod
    def get_actions(cur_level: int) -> list:
        if cur_level == 1:
            return [CITY_LEVEL_UP.WORKSHOP, CITY_LEVEL_UP.EXPLORER]
        elif cur_level == 2:
            return [CITY_LEVEL_UP.CITY_WALL, CITY_LEVEL_UP.RESOURCES]
        elif cur_level == 3:
            return [CITY_LEVEL_UP.POP_GROWTH, CITY_LEVEL_UP.BORDER_GROWTH]
        else:
            return [CITY_LEVEL_UP.PARK, CITY_LEVEL_UP.SUPERUNIT]

    def valid_type(self, city_level: int) -> bool:
        if city_level == 1 and self in (CITY_LEVEL_UP.WORKSHOP, CITY_LEVEL_UP.EXPLORER):
            return True
        if city_level == 2 and self in (CITY_LEVEL_UP.CITY_WALL, CITY_LEVEL_UP.RESOURCES):
            return True
        if city_level == 3 and self in (CITY_LEVEL_UP.POP_GROWTH, CITY_LEVEL_UP.BORDER_GROWTH):
            return True
        return city_level >= 4 and self in (CITY_LEVEL_UP.PARK, CITY_LEVEL_UP.SUPERUNIT)

    def get_level_up_points(self) -> int:
        if self._level == 1:
            return 100
        return 50 - self._level * 5

    def grants_monument(self) -> bool:
        from tribes.config import PARK_OF_FORTUNE_LEVEL
        return self._level == PARK_OF_FORTUNE_LEVEL


# ---------------------------------------------------------------------------
# UNIT
# ---------------------------------------------------------------------------

class UNIT(Enum):
    WARRIOR    = (0,  "img/unit/warrior/",    "img/weapons/melee/tile006.png", None,          None)
    RIDER      = (1,  "img/unit/rider/",      "img/weapons/melee/tile001.png", None,          "RIDING")
    DEFENDER   = (2,  "img/unit/defender/",   "img/weapons/melee/tile002.png", None,          "SHIELDS")
    SWORDMAN   = (3,  "img/unit/swordsman/",  "img/weapons/melee/tile000.png", None,          "SMITHERY")
    ARCHER     = (4,  "img/unit/archer/",     "img/weapons/arrows/",           None,          "ARCHERY")
    CATAPULT   = (5,  "img/unit/catapult/",   "img/weapons/bombs/rock.png",    None,          "MATHEMATICS")
    KNIGHT     = (6,  "img/unit/knight/",     "img/weapons/melee/spear.png",   None,          "CHIVALRY")
    MIND_BENDER = (7, "img/unit/mind_bender/","img/weapons/effects/bender/",   None,          "PHILOSOPHY")  # noqa: E221,E201
    BOAT       = (8,  "img/unit/boat/",       "img/weapons/arrows/boat.png",   None,          "SAILING")
    SHIP       = (9,  "img/unit/ship/",       "img/weapons/bombs/",            None,          "SAILING")
    BATTLESHIP = (10, "img/unit/battleship/", "img/weapons/bombs/",            None,          "NAVIGATION")
    SUPERUNIT  = (11, "img/unit/superunit/",  "img/weapons/melee/tile003.png", None,          None)

    def __init__(self, key: int, image_file: str, weapon_file: str,
                 _points_placeholder, tech_name: Optional[str]) -> None:
        self._key = key
        self._image_file = image_file
        self._weapon_file = weapon_file
        self._tech_name = tech_name
        self._cost: int = 0
        self._points: int = 0

    @staticmethod
    def string_to_type(type_str: str) -> Optional[UNIT]:
        try:
            return UNIT[type_str]
        except KeyError:
            return None

    @staticmethod
    def get_type_by_key(key: int) -> Optional[UNIT]:
        for u in UNIT:
            if u._key == key:
                return u
        return None

    @staticmethod
    def get_spawnable_types() -> list:
        return [u for u in UNIT if u.spawnable()]

    @staticmethod
    def create_unit(pos: "Vector2d", kills: int, is_veteran: bool,
                    owner_id: int, tribe_id: int, unit_type: UNIT) -> "Unit":
        """Factory: creates a Unit subclass instance."""
        from tribes.actors.units.warrior import Warrior
        from tribes.actors.units.rider import Rider
        from tribes.actors.units.defender import Defender
        from tribes.actors.units.swordman import Swordman
        from tribes.actors.units.archer import Archer
        from tribes.actors.units.catapult import Catapult
        from tribes.actors.units.knight import Knight
        from tribes.actors.units.mind_bender import MindBender
        from tribes.actors.units.boat import Boat
        from tribes.actors.units.ship import Ship
        from tribes.actors.units.battleship import Battleship
        from tribes.actors.units.super_unit import SuperUnit

        mapping = {
            UNIT.WARRIOR:    Warrior,
            UNIT.RIDER:      Rider,
            UNIT.DEFENDER:   Defender,
            UNIT.SWORDMAN:   Swordman,
            UNIT.ARCHER:     Archer,
            UNIT.CATAPULT:   Catapult,
            UNIT.KNIGHT:     Knight,
            UNIT.MIND_BENDER: MindBender,
            UNIT.BOAT:       Boat,
            UNIT.SHIP:       Ship,
            UNIT.BATTLESHIP: Battleship,
            UNIT.SUPERUNIT:  SuperUnit,
        }
        cls = mapping.get(unit_type)
        if cls is None:
            logger.warning(f"create_unit(): type {unit_type} not implemented.")
            return None
        return cls(pos, kills, is_veteran, owner_id, tribe_id)

    def get_key(self) -> int:
        return self._key

    def get_cost(self) -> int:
        return self._cost

    def get_points(self) -> int:
        return self._points

    def get_technology_requirement(self) -> Optional[TECHNOLOGY]:
        if self._tech_name is None:
            return None
        return TECHNOLOGY[self._tech_name]

    def spawnable(self) -> bool:
        return self not in (UNIT.BOAT, UNIT.SHIP, UNIT.BATTLESHIP, UNIT.SUPERUNIT)

    def is_water_unit(self) -> bool:
        return self in (UNIT.BOAT, UNIT.SHIP, UNIT.BATTLESHIP)

    def is_ranged(self) -> bool:
        return self in (UNIT.BOAT, UNIT.SHIP, UNIT.BATTLESHIP, UNIT.ARCHER, UNIT.CATAPULT)

    def can_fortify(self) -> bool:
        return self in (
            UNIT.WARRIOR, UNIT.RIDER, UNIT.ARCHER,
            UNIT.DEFENDER, UNIT.SWORDMAN, UNIT.KNIGHT,
        )


def _wire_unit_costs() -> None:
    from tribes import config as cfg
    _unit_data = {
        UNIT.WARRIOR:    (cfg.WARRIOR_COST,    cfg.WARRIOR_POINTS),
        UNIT.RIDER:      (cfg.RIDER_COST,      cfg.RIDER_POINTS),
        UNIT.DEFENDER:   (cfg.DEFENDER_COST,   cfg.DEFENDER_POINTS),
        UNIT.SWORDMAN:   (cfg.SWORDMAN_COST,   cfg.SWORDMAN_POINTS),
        UNIT.ARCHER:     (cfg.ARCHER_COST,     cfg.ARCHER_POINTS),
        UNIT.CATAPULT:   (cfg.CATAPULT_COST,   cfg.CATAPULT_POINTS),
        UNIT.KNIGHT:     (cfg.KNIGHT_COST,     cfg.KNIGHT_POINTS),
        UNIT.MIND_BENDER:(cfg.MINDBENDER_COST, cfg.MINDBENDER_POINTS),
        UNIT.BOAT:       (cfg.BOAT_COST,       cfg.BOAT_POINTS),
        UNIT.SHIP:       (cfg.SHIP_COST,       cfg.SHIP_POINTS),
        UNIT.BATTLESHIP: (cfg.BATTLESHIP_COST, cfg.BATTLESHIP_POINTS),
        UNIT.SUPERUNIT:  (cfg.SUPERUNIT_COST,  cfg.SUPERUNIT_POINTS),
    }
    for member, (cost, points) in _unit_data.items():
        member._cost = cost
        member._points = points


# ---------------------------------------------------------------------------
# DIRECTIONS
# ---------------------------------------------------------------------------

class DIRECTIONS(Enum):
    NONE  = (0,  0)
    LEFT  = (-1, 0)
    RIGHT = (1,  0)
    UP    = (0, -1)
    DOWN  = (0,  1)

    def __init__(self, x: int, y: int) -> None:
        self._x = x
        self._y = y

    def x(self) -> int:
        return self._x

    def y(self) -> int:
        return self._y


# ---------------------------------------------------------------------------
# GAME_MODE
# ---------------------------------------------------------------------------

class GAME_MODE(Enum):
    CAPITALS = 0
    SCORE    = 1

    def __init__(self, key: int) -> None:
        self._key = key

    def get_key(self) -> int:
        return self._key

    def get_max_turns(self) -> int:
        from tribes import constants as C
        return C.MAX_TURNS_CAPITALS if self is GAME_MODE.CAPITALS else C.MAX_TURNS

    @staticmethod
    def get_type_by_key(key: int) -> Optional[GAME_MODE]:
        for g in GAME_MODE:
            if g._key == key:
                return g
        return None


# ---------------------------------------------------------------------------
# RESULT
# ---------------------------------------------------------------------------

class RESULT(Enum):
    WIN        = 0
    LOSS       = 1
    INCOMPLETE = 2

    def __init__(self, key: int) -> None:
        self._key = key

    def get_key(self) -> int:
        return self._key

    @staticmethod
    def get_type_by_key(key: int) -> Optional[RESULT]:
        for r in RESULT:
            if r._key == key:
                return r
        return None


# ---------------------------------------------------------------------------
# ACTION
# ---------------------------------------------------------------------------

class ACTION(Enum):
    # Each member uses a unique ordinal as the first element to prevent
    # Python enum from aliasing members that share (img_path, tech_name).
    # city
    BUILD              = ( 0, None,                           None)
    BURN_FOREST        = ( 1, None,                           "CHIVALRY")
    CLEAR_FOREST       = ( 2, None,                           "FORESTRY")
    DESTROY            = ( 3, None,                           "CONSTRUCTION")
    GROW_FOREST        = ( 4, None,                           "SPIRITUALISM")
    LEVEL_UP           = ( 5, None,                           None)
    RESOURCE_GATHERING = ( 6, None,                           None)
    SPAWN              = ( 7, None,                           None)
    # tribe
    BUILD_ROAD         = ( 8, None,                           "ROADS")
    END_TURN           = ( 9, None,                           None)
    RESEARCH_TECH      = (10, None,                           None)
    DECLARE_WAR        = (11, None,                           None)
    SEND_STARS         = (12, None,                           None)
    # unit
    ATTACK             = (13, "img/actions/attack.png",       None)
    CAPTURE            = (14, "img/actions/capture.png",      None)
    CONVERT            = (15, "img/actions/convert.png",      None)
    DISBAND            = (16, "img/actions/disband.png",      "FREE_SPIRIT")
    EXAMINE            = (17, "img/actions/examine.png",      None)
    HEAL_OTHERS        = (18, "img/actions/heal2.png",        None)
    MAKE_VETERAN       = (19, None,                           None)
    MOVE               = (20, "img/actions/move.png",         None)
    RECOVER            = (21, None,                           None)
    # other
    CLIMB_MOUNTAIN     = (22, None,                           "CLIMBING")
    UPGRADE_BOAT       = (23, "img/actions/upgrade.png",      "SAILING")
    UPGRADE_SHIP       = (24, "img/actions/upgrade.png",      "NAVIGATION")

    def __init__(self, _key: int, img_path: Optional[str], tech_name: Optional[str]) -> None:
        self._img_path = img_path
        self._tech_name = tech_name

    def get_technology_requirement(self) -> Optional[TECHNOLOGY]:
        if self._tech_name is None:
            return None
        return TECHNOLOGY[self._tech_name]


# ---------------------------------------------------------------------------
# Deferred wiring (must happen after all enum classes are defined)
# ---------------------------------------------------------------------------

_wire_building_costs()
_wire_unit_costs()
