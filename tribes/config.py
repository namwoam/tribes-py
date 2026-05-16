"All game configuration constants ported from TribesConfig.java."
from __future__ import annotations

# ---------------------------------------------------------------------------
# UNITS
# ---------------------------------------------------------------------------

# Warrior
WARRIOR_ATTACK: int    = 2
WARRIOR_DEFENCE: int   = 2
WARRIOR_MOVEMENT: int  = 1
WARRIOR_MAX_HP: int    = 10
WARRIOR_RANGE: int     = 1
WARRIOR_COST: int      = 2
WARRIOR_POINTS: int    = 10

# Archer
ARCHER_ATTACK: int     = 2
ARCHER_DEFENCE: int    = 1
ARCHER_MOVEMENT: int   = 1
ARCHER_MAX_HP: int     = 10
ARCHER_RANGE: int      = 2
ARCHER_COST: int       = 3
ARCHER_POINTS: int     = 15

# Catapult
CATAPULT_ATTACK: int   = 4
CATAPULT_DEFENCE: int  = 0
CATAPULT_MOVEMENT: int = 1
CATAPULT_MAX_HP: int   = 10
CATAPULT_RANGE: int    = 3
CATAPULT_COST: int     = 8
CATAPULT_POINTS: int   = 40

# Swordsman
SWORDMAN_ATTACK: int   = 3
SWORDMAN_DEFENCE: int  = 3
SWORDMAN_MOVEMENT: int = 1
SWORDMAN_MAX_HP: int   = 15
SWORDMAN_RANGE: int    = 1
SWORDMAN_COST: int     = 5
SWORDMAN_POINTS: int   = 25

# MindBender
MINDBENDER_ATTACK: int   = 0
MINDBENDER_DEFENCE: int  = 1
MINDBENDER_MOVEMENT: int = 1
MINDBENDER_MAX_HP: int   = 10
MINDBENDER_RANGE: int    = 1
MINDBENDER_COST: int     = 5
MINDBENDER_HEAL: int     = 4
MINDBENDER_POINTS: int   = 25

# Defender
DEFENDER_ATTACK: int   = 1
DEFENDER_DEFENCE: int  = 3
DEFENDER_MOVEMENT: int = 1
DEFENDER_MAX_HP: int   = 15
DEFENDER_RANGE: int    = 1
DEFENDER_COST: int     = 3
DEFENDER_POINTS: int   = 15

# Knight
KNIGHT_ATTACK: int     = 4
KNIGHT_DEFENCE: int    = 1
KNIGHT_MOVEMENT: int   = 3
KNIGHT_MAX_HP: int     = 15
KNIGHT_RANGE: int      = 1
KNIGHT_COST: int       = 8
KNIGHT_POINTS: int     = 40

# Rider
RIDER_ATTACK: int      = 2
RIDER_DEFENCE: int     = 1
RIDER_MOVEMENT: int    = 2
RIDER_MAX_HP: int      = 10
RIDER_RANGE: int       = 1
RIDER_COST: int        = 3
RIDER_POINTS: int      = 15

# Boat
BOAT_ATTACK: int       = 1
BOAT_DEFENCE: int      = 1
BOAT_MOVEMENT: int     = 2
BOAT_RANGE: int        = 2
BOAT_COST: int         = 0
BOAT_POINTS: int       = 0

# Ship
SHIP_ATTACK: int       = 2
SHIP_DEFENCE: int      = 2
SHIP_MOVEMENT: int     = 3
SHIP_RANGE: int        = 2
SHIP_COST: int         = 5
SHIP_POINTS: int       = 0

# Battleship
BATTLESHIP_ATTACK: int   = 4
BATTLESHIP_DEFENCE: int  = 3
BATTLESHIP_MOVEMENT: int = 3
BATTLESHIP_RANGE: int    = 2
BATTLESHIP_COST: int     = 15
BATTLESHIP_POINTS: int   = 0

# Superunit
SUPERUNIT_ATTACK: int    = 5
SUPERUNIT_DEFENCE: int   = 4
SUPERUNIT_MOVEMENT: int  = 1
SUPERUNIT_MAX_HP: int    = 40
SUPERUNIT_RANGE: int     = 1
SUPERUNIT_COST: int      = 10
SUPERUNIT_POINTS: int    = 50

# Explorer
NUM_STEPS: int = 15

# General Unit constants
ATTACK_MODIFIER: float              = 4.5
DEFENCE_BONUS: float                = 1.5
DEFENCE_IN_WALLS: float             = 4.0
VETERAN_KILLS: int                  = 3
VETERAN_PLUS_HP: int                = 5
RECOVER_PLUS_HP: int                = 2
RECOVER_IN_BORDERS_PLUS_HP: int     = 2

# ---------------------------------------------------------------------------
# BUILDINGS
# ---------------------------------------------------------------------------

FARM_COST: int          = 5
FARM_BONUS: int         = 2

WIND_MILL_COST: int     = 5
WIND_MILL_BONUS: int    = 1

LUMBER_HUT_COST: int    = 2
LUMBER_HUT_BONUS: int   = 1

SAW_MILL_COST: int      = 5
SAW_MILL_BONUS: int     = 1

MINE_COST: int          = 5
MINE_BONUS: int         = 2

FORGE_COST: int         = 5
FORGE_BONUS: int        = 2

PORT_COST: int          = 10
PORT_BONUS: int         = 2
PORT_TRADE_DISTANCE: int = 4

CUSTOMS_COST: int       = 5
CUSTOMS_BONUS: int      = 2

MONUMENT_BONUS: int     = 3
MONUMENT_POINTS: int    = 400
EMPERORS_TOMB_STARS: int = 100
GATE_OF_POWER_KILLS: int = 10
GRAND_BAZAR_CITIES: int  = 5
ALTAR_OF_PEACE_TURNS: int = 5
PARK_OF_FORTUNE_LEVEL: int = 5

TEMPLE_COST: int        = 20
TEMPLE_FOREST_COST: int = 15
TEMPLE_BONUS: int       = 1
TEMPLE_TURNS_TO_SCORE: int = 3
TEMPLE_POINTS: list     = [100, 50, 50, 50, 150]

# ---------------------------------------------------------------------------
# RESOURCES
# ---------------------------------------------------------------------------

ANIMAL_COST: int   = 2
FISH_COST: int     = 2
WHALES_COST: int   = 0
FRUIT_COST: int    = 2
ANIMAL_POP: int    = 1
FISH_POP: int      = 1
WHALES_STARS: int  = 10
FRUIT_POP: int     = 1

# Resource constraints (typed references - imported lazily to avoid circular)

def _get_farm_res_constraint():
    from tribes.types import RESOURCE
    return RESOURCE.CROPS


def _get_mine_res_constraint():
    from tribes.types import RESOURCE
    return RESOURCE.ORE


# Convenience aliases for modules that import these directly
@property
def FARM_RES_CONSTRAINT():
    return _get_farm_res_constraint()


@property
def MINE_RES_CONSTRAINT():
    return _get_mine_res_constraint()

# ---------------------------------------------------------------------------
# ROAD
# ---------------------------------------------------------------------------

ROAD_COST: int = 2

# ---------------------------------------------------------------------------
# CITY
# ---------------------------------------------------------------------------

CITY_LEVEL_UP_WORKSHOP_PROD: int  = 1
CITY_LEVEL_UP_RESOURCES: int      = 5
CITY_LEVEL_UP_POP_GROWTH: int     = 3
CITY_LEVEL_UP_PARK: int           = 250
CITY_BORDER_POINTS: int           = 20
CITY_CENTRE_POINTS: int           = 100
PROD_CAPITAL_BONUS: int           = 1
EXPLORER_CLEAR_RANGE: int         = 1
FIRST_CITY_CLEAR_RANGE: int       = 2
NEW_CITY_CLEAR_RANGE: int         = 1
CITY_EXPANSION_TILES: int         = 1
POINTS_PER_POPULATION: int        = 5

# ---------------------------------------------------------------------------
# DIPLOMACY
# ---------------------------------------------------------------------------

ALLEGIANCE_MAX: int        = 60
ATTACK_REPERCUSSION: int   = -5
CAPTURE_REPERCUSSION: int  = -30
CONVERT_REPERCUSSION: int  = -5
MIN_STARS_SEND: int        = 15

# ---------------------------------------------------------------------------
# RESEARCH
# ---------------------------------------------------------------------------

TECH_BASE_COST: int        = 4
TECH_DISCOUNT_VALUE: float = 0.2
TECH_TIER_POINTS: int      = 100

# TECH_DISCOUNT is Types.TECHNOLOGY.PHILOSOPHY — imported lazily

def get_tech_discount():
    from tribes.types import TECHNOLOGY
    return TECHNOLOGY.PHILOSOPHY


# ---------------------------------------------------------------------------
# TRIBES
# ---------------------------------------------------------------------------

INITIAL_STARS: int = 5

# ---------------------------------------------------------------------------
# ACTIONS
# ---------------------------------------------------------------------------

CLEAR_FOREST_STAR: int    = 2
GROW_FOREST_COST: int     = 5
BURN_FOREST_COST: int     = 5
CLEAR_VIEW_POINTS: int    = 5

# ---------------------------------------------------------------------------
# MAP
# ---------------------------------------------------------------------------

DEFAULT_MAP_SIZE: list = [-1, 11, 14, 16, 18, 20, 22, 24]
