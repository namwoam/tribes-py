"Game Board, ported from Board.java."
from __future__ import annotations

import logging
import random as _random
from typing import TYPE_CHECKING, Optional

from tribes.types import TERRAIN, RESOURCE, BUILDING, TECHNOLOGY, UNIT as UNIT_TYPE, TURN_STATUS
from tribes.utils.vector2d import Vector2d
from tribes import config as cfg
from tribes.diplomacy import Diplomacy

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.actors.actor import Actor
    from tribes.actors.city import City
    from tribes.actors.tribe import Tribe
    from tribes.actors.units.unit import Unit
    from tribes.game.trade_network import TradeNetwork


class Board:
    """Game board holding terrains, units, buildings and city ownership."""

    def __init__(self) -> None:
        self._size: int = 0
        self._terrains: list[list[Optional[TERRAIN]]] = []
        self._resources: list[list[Optional[RESOURCE]]] = []
        self._buildings: list[list[Optional[BUILDING]]] = []
        self._units: list[list[int]] = []          # 0 = empty
        self._tile_city_id: list[list[int]] = []   # -1 = no city
        self._tribes: list[Tribe] = []
        self._capital_ids: list[int] = []
        self._game_actors: dict[int, Actor] = {}
        self._actor_id_counter: int = 0
        self._active_tribe_id: int = -1
        self._trade_network: Optional[TradeNetwork] = None
        self._diplomacy: Optional[Diplomacy] = None
        self._is_native: bool = True

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def init(self, size: int, tribes: list[Tribe]) -> None:
        from tribes.game.trade_network import TradeNetwork

        self._size = size
        self._capital_ids = [-1] * len(tribes)
        self._terrains = [[None] * size for _ in range(size)]
        self._resources = [[None] * size for _ in range(size)]
        self._buildings = [[None] * size for _ in range(size)]
        self._units = [[0] * size for _ in range(size)]
        self._tile_city_id = [[-1] * size for _ in range(size)]
        self._trade_network = TradeNetwork(size)
        self._diplomacy = Diplomacy(len(tribes))
        self._is_native = True

        for t in tribes:
            t.init_obs_grid(size)

        self._assign_tribes(tribes)

    def _assign_tribes(self, tribes: list[Tribe]) -> None:
        self._tribes = list(tribes)
        for i, t in enumerate(self._tribes):
            t.tribe_id = i
            t.actor_id = i

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    def copy(self, partial_obs: bool = False, player_id: int = -1) -> Board:
        cb = Board()
        cb._size = self._size
        cb._active_tribe_id = self._active_tribe_id
        cb._actor_id_counter = self._actor_id_counter
        cb._is_native = False

        n = self._size
        cb._terrains = [[None] * n for _ in range(n)]
        cb._resources = [[None] * n for _ in range(n)]
        cb._buildings = [[None] * n for _ in range(n)]
        cb._units = [[0] * n for _ in range(n)]
        cb._tile_city_id = [[-1] * n for _ in range(n)]

        from tribes.game.trade_network import TradeNetwork
        cb._trade_network = TradeNetwork(n)
        cb._diplomacy = self._diplomacy.copy() if self._diplomacy else Diplomacy(len(self._tribes))

        cb._capital_ids = list(self._capital_ids)

        for x in range(n):
            for y in range(n):
                if not partial_obs or self._tribes[player_id].is_visible(x, y):
                    cb._units[x][y] = self._units[x][y]
                    cb.set_terrain_at(x, y, self._terrains[x][y])
                    cb.set_resource_at(x, y, self._mask_resource(player_id, x, y))
                    cb.set_building_at(x, y, self._buildings[x][y])
                    cb._tile_city_id[x][y] = self._tile_city_id[x][y]
                    cb._trade_network.set_trade_network_value(
                        x, y, self._trade_network.get_trade_network_value(x, y))
                else:
                    cb.set_terrain_at(x, y, TERRAIN.FOG)

        # Copy tribes
        cb._tribes = []
        for i, t in enumerate(self._tribes):
            hide = (i != player_id) and partial_obs
            cb._tribes.append(t.copy(hide))

        # Deep copy actors
        cb._game_actors = {}
        from tribes.actors.city import City as CityActor
        from tribes.actors.units.unit import Unit as UnitActor

        for act in self._game_actors.values():
            act_id = act.actor_id
            act_tribe_id = act.tribe_id
            actor_visible = (player_id == -1 or
                             self._tribes[player_id].is_visible(
                                 act.get_position().x, act.get_position().y))

            if act_tribe_id == player_id or not partial_obs or actor_visible:
                hide = (act_tribe_id != player_id) and partial_obs
                actor_copy = act.copy(hide)
                cb._game_actors[act_id] = actor_copy

                if hide and actor_visible:
                    t_id = actor_copy.tribe_id
                    if isinstance(actor_copy, CityActor):
                        cb._tribes[t_id].add_city(actor_copy.actor_id)
                    elif isinstance(actor_copy, UnitActor):
                        cb._tribes[t_id].add_extra_unit(actor_copy)

        return cb

    def _mask_resource(self, player_id: int, x: int, y: int) -> Optional[RESOURCE]:
        if player_id == -1:
            return self._resources[x][y]
        r = self._resources[x][y]
        if r is None:
            return None
        tt = self._tribes[player_id].get_tech_tree()
        try:
            if r is RESOURCE.CROPS and not tt.is_researched(TECHNOLOGY.ORGANIZATION):
                return None
            if r is RESOURCE.ORE and not tt.is_researched(TECHNOLOGY.CLIMBING):
                return None
            if r is RESOURCE.WHALES and not tt.is_researched(TECHNOLOGY.FISHING):
                return None
        except Exception:
            return None
        return r

    # ------------------------------------------------------------------
    # Unit movement
    # ------------------------------------------------------------------

    def push_unit(self, tribe: Tribe, to_push: Unit,
                  start_x: int, start_y: int, r: _random.Random) -> bool:
        x_push = [0, -1, 0, 1, -1, -1, 1, 1]
        y_push = [1, 0, -1, 0, 1, -1, -1, 1]
        idx = 0
        pushed = False
        while not pushed and idx < len(x_push):
            x = start_x + x_push[idx]
            y = start_y + y_push[idx]
            if 0 <= x < self._size and 0 <= y < self._size:
                pushed = self.try_push(tribe, to_push, start_x, start_y, x, y, r)
            idx += 1
        to_push.set_status(TURN_STATUS.PUSHED)
        return pushed

    def try_push(self, tribe: Tribe, to_push: Unit,
                 start_x: int, start_y: int,
                 x: int, y: int, r: _random.Random) -> bool:
        u = self.get_unit_at(x, y)
        if u is not None:
            return False

        terrain = self._terrains[x][y]
        tribe_id = tribe.tribe_id

        if terrain is TERRAIN.MOUNTAIN:
            if self._tribes[tribe_id].get_tech_tree().is_researched(TECHNOLOGY.CLIMBING):
                self.move_unit(to_push, start_x, start_y, x, y, r)
                return True
            return False

        b = self._buildings[x][y]
        if terrain in (TERRAIN.SHALLOW_WATER, TERRAIN.DEEP_WATER):
            if to_push.get_type().is_water_unit():
                return True
            if b is BUILDING.PORT:
                c = self.get_city_in_borders(x, y)
                if c is not None and c.tribe_id == tribe_id:
                    self.embark(to_push, tribe, x, y)
                    return True
            return False

        self.move_unit(to_push, start_x, start_y, x, y, r)
        return True

    def embark(self, unit: Unit, tribe: Tribe, x: int, y: int) -> None:
        from tribes.actors.units.boat import Boat
        city = self._game_actors.get(unit.get_city_id())
        self.remove_unit_from_board(unit)
        self.remove_unit_from_city(unit, city, tribe)

        new_pos = Vector2d(x, y)
        boat = UNIT_TYPE.create_unit(new_pos, unit.get_kills(), unit.is_veteran(),
                                     unit.get_city_id(), unit.tribe_id, UNIT_TYPE.BOAT)
        boat.set_current_hp(unit.get_current_hp())
        boat.set_max_hp(unit.get_max_hp())
        boat.set_base_land_unit(unit.get_type())
        self.add_unit(city, boat)

    def disembark(self, unit: Unit, tribe: Tribe, x: int, y: int) -> None:
        city = self._game_actors.get(unit.get_city_id())
        self.remove_unit_from_board(unit)
        self.remove_unit_from_city(unit, city, tribe)
        base_land_unit = self.get_base_land_unit(unit)
        if base_land_unit is None:
            logger.error(f"disembark: base land unit is None for {unit.get_type()}")
            base_land_unit = UNIT_TYPE.WARRIOR

        new_pos = Vector2d(x, y)
        new_unit = UNIT_TYPE.create_unit(new_pos, unit.get_kills(), unit.is_veteran(),
                                         unit.get_city_id(), unit.tribe_id, base_land_unit)
        new_unit.set_current_hp(unit.get_current_hp())
        new_unit.set_max_hp(unit.get_max_hp())
        self.add_unit(city, new_unit)

    def get_base_land_unit(self, unit: Unit) -> Optional[UNIT_TYPE]:
        ut = unit.get_type()
        if ut is UNIT_TYPE.BOAT:
            return unit.get_base_land_unit()
        if ut is UNIT_TYPE.SHIP:
            return unit.get_base_land_unit()
        if ut is UNIT_TYPE.BATTLESHIP:
            return unit.get_base_land_unit()
        logger.error(f"get_base_land_unit: unexpected type {ut}")
        return None

    def move_unit(self, unit: Unit, x0: int, y0: int,
                  xf: int, yf: int, r: _random.Random) -> None:
        self._units[x0][y0] = 0
        self._units[xf][yf] = unit.actor_id
        unit.set_position(xf, yf)
        t = self._tribes[unit.tribe_id]

        partial_obs_range = 1
        if (self.get_terrain_at(xf, yf) is TERRAIN.MOUNTAIN
                or unit.get_type() is UNIT_TYPE.BATTLESHIP):
            partial_obs_range += 1

        network_update = t.clear_view(xf, yf, partial_obs_range, r, self)
        if network_update:
            self._trade_network.compute_trade_network_tribe(self, t)

    def launch_explorer(self, x0: int, y0: int,
                        tribe_id: int, rnd: _random.Random) -> None:
        current_pos = Vector2d(x0, y0)
        for _ in range(cfg.NUM_STEPS):
            j = 0
            moved = False
            while not moved and j < cfg.NUM_STEPS * 3:
                neighs = current_pos.neighborhood(1, 0, self._size)
                nxt = neighs[rnd.randint(0, len(neighs) - 1)]
                if self.traversable(nxt.x, nxt.y, tribe_id):
                    moved = True
                    current_pos = Vector2d(nxt.x, nxt.y)
                    update_net = self._tribes[tribe_id].clear_view(
                        current_pos.x, current_pos.y,
                        cfg.EXPLORER_CLEAR_RANGE, rnd, self)
                    if update_net:
                        self._trade_network.compute_trade_network_tribe(
                            self, self._tribes[tribe_id])
                j += 1

    def traversable(self, x: int, y: int, tribe_id: int) -> bool:
        tt = self._tribes[tribe_id].get_tech_tree()
        if self._terrains[x][y] is TERRAIN.MOUNTAIN and not tt.is_researched(TECHNOLOGY.CLIMBING):
            return False
        if self._terrains[x][y] is TERRAIN.SHALLOW_WATER and not tt.is_researched(TECHNOLOGY.SAILING):
            return False
        if self._terrains[x][y] is TERRAIN.DEEP_WATER:
            return tt.is_researched(TECHNOLOGY.NAVIGATION)
        return True

    # ------------------------------------------------------------------
    # City tiles
    # ------------------------------------------------------------------

    def assign_city_tiles(self, c: City, radius: int) -> None:
        city_pos = c.get_position()
        t = self.get_tribe(c.tribe_id)
        tiles = city_pos.neighborhood(radius, 0, self._size)
        tiles.append(Vector2d(city_pos.x, city_pos.y))
        for tile in tiles:
            if self._tile_city_id[tile.x][tile.y] == -1:
                self._tile_city_id[tile.x][tile.y] = c.actor_id
                t.add_score(cfg.CITY_BORDER_POINTS)
                c.add_points_worth(cfg.CITY_BORDER_POINTS)

    def expand_border(self, city: City) -> None:
        city.set_bound(city.get_bound() + cfg.CITY_EXPANSION_TILES)
        self.assign_city_tiles(city, city.get_bound())

    def get_city_tiles(self, city_id: int) -> list[Vector2d]:
        tiles: list[Vector2d] = []
        target_city: City = self._game_actors.get(city_id)
        if target_city is None:
            return tiles
        target_pos = target_city.get_position()
        level = target_city.get_level()
        radius = 1 if level < 4 else 2

        for i in range(target_pos.x - radius, target_pos.x + radius + 1):
            for j in range(target_pos.y - radius, target_pos.y + radius + 1):
                if 0 <= i < self._size and 0 <= j < self._size:
                    if self._tile_city_id[i][j] == city_id:
                        tiles.append(Vector2d(i, j))
        return tiles

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------

    def capture(self, game_state, capturing_tribe: Tribe,
                x: int, y: int) -> bool:
        rnd = game_state.get_random_generator()
        ter = self._terrains[x][y]

        if ter is TERRAIN.VILLAGE:
            from tribes.actors.city import City as CityActor
            new_city = CityActor(x, y, capturing_tribe.tribe_id)
            self.add_city_to_tribe(new_city, rnd)
            self.assign_city_tiles(new_city, new_city.get_bound())
            self.set_terrain_at(x, y, TERRAIN.CITY)
            self._move_one_to_new_city(new_city, capturing_tribe, rnd)
            capturing_tribe.add_score(cfg.CITY_CENTRE_POINTS)

        elif ter is TERRAIN.CITY:
            captured_city: City = self._game_actors.get(self._tile_city_id[x][y])
            previous_owner = self._tribes[captured_city.tribe_id]

            capturing_tribe.captured_city(game_state, captured_city)
            previous_owner.lost_city(game_state, captured_city)

            self._move_all_from_city(captured_city, previous_owner, rnd)
            self._move_one_to_new_city(captured_city, capturing_tribe, rnd)

            if previous_owner.get_num_cities() == 0 and game_state.is_native():
                previous_owner.manage_loss(game_state)

        else:
            logger.warning(f"capture: tribe {capturing_tribe.tribe_id} trying to capture non-city at {x},{y}")
            return False

        self._trade_network.set_trade_network(self, x, y, True)
        return True

    def _move_one_to_new_city(self, dest_city: City, tribe: Tribe,
                               rnd: _random.Random) -> None:
        owns_capital = tribe.controls_capital()
        capital: City = self.get_actor(tribe.get_capital_id())
        cities = list(tribe.get_cities_id())
        if capital.actor_id in cities:
            cities.remove(capital.actor_id)

        if owns_capital and capital.get_num_units() > 0:
            self._move_last_unit_from_city(capital, dest_city)
        else:
            moved = False
            rnd.shuffle(cities)
            while not moved and cities:
                orig_city: City = self.get_actor(cities.pop(0))
                if orig_city.get_num_units() > 0:
                    self._move_last_unit_from_city(orig_city, dest_city)
                    moved = True

    def _move_all_from_city(self, from_city: City, tribe: Tribe,
                             rnd: _random.Random) -> None:
        owns_capital = tribe.controls_capital()
        capital: City = self.get_actor(tribe.get_capital_id())

        if owns_capital:
            while capital.can_add_unit() and from_city.get_num_units() > 0:
                self._move_last_unit_from_city(from_city, capital)

        if from_city.get_num_units() > 0:
            cities = list(tribe.get_cities_id())
            if capital.actor_id in cities:
                cities.remove(capital.actor_id)
            rnd.shuffle(cities)
            while cities and from_city.get_num_units() > 0:
                dest_city: City = self.get_actor(cities.pop(0))
                while dest_city.can_add_unit() and from_city.get_num_units() > 0:
                    self._move_last_unit_from_city(from_city, dest_city)

            # remaining go to tribe extra units
            while from_city.get_num_units() > 0:
                unit_id = from_city.get_units_id()[0]
                removed_unit = self._game_actors.get(unit_id)
                if removed_unit is not None:
                    tribe.add_extra_unit(removed_unit)
                    from_city.remove_unit(unit_id)
                else:
                    logger.error(f"_move_all_from_city: unit {unit_id} not found")
                    break

    def _move_last_unit_from_city(self, orig_city: City, target_city: City) -> None:
        index = orig_city.get_num_units() - 1
        actor_id = orig_city.remove_unit_by_index(index)
        target_city.add_unit(actor_id)
        removed_unit = self._game_actors.get(actor_id)
        if removed_unit is not None:
            removed_unit.set_city_id(target_city.actor_id)

    # ------------------------------------------------------------------
    # City management
    # ------------------------------------------------------------------

    def add_city_to_tribe(self, c: City, r: _random.Random) -> None:
        self._add_actor(c)
        if c.is_capital():
            self._set_capital_id(c.tribe_id, c.actor_id)
        self._tribes[c.tribe_id].add_city(c.actor_id)
        self._tribes[c.tribe_id].clear_view(
            c.get_position().x, c.get_position().y,
            cfg.NEW_CITY_CLEAR_RANGE, r, self.copy())
        self._trade_network.set_trade_network(
            self, c.get_position().x, c.get_position().y, True)

    def _set_capital_id(self, tribe_id: int, capital_id: int) -> None:
        self._tribes[tribe_id].set_capital_id(capital_id)
        self._capital_ids[tribe_id] = capital_id

    # ------------------------------------------------------------------
    # Unit management
    # ------------------------------------------------------------------

    def add_unit(self, c: City, u: Unit) -> None:
        self._add_actor(u)
        pos = u.get_position()
        self._units[pos.x][pos.y] = u.actor_id
        if u.get_city_id() != -1:
            c.add_unit(u.actor_id)
        elif u.actor_id not in self._tribes[u.tribe_id].get_extra_units():
            self._tribes[u.tribe_id].add_extra_unit(u)

    def remove_unit_from_board(self, u: Unit) -> None:
        pos = u.get_position()
        self._units[pos.x][pos.y] = 0
        self._remove_actor(u.actor_id)

    def remove_unit_from_city(self, u: Unit, city: Optional[City],
                               tribe: Tribe) -> None:
        if u.get_city_id() != -1 and city is not None:
            city.remove_unit(u.actor_id)
        else:
            tribe.remove_extra_unit(u)

    # ------------------------------------------------------------------
    # Actors
    # ------------------------------------------------------------------

    def _add_actor(self, actor: Actor) -> None:
        self._actor_id_counter += 1
        self._game_actors[self._actor_id_counter] = actor
        actor.actor_id = self._actor_id_counter

    def _add_actor_with_id(self, actor: Actor, actor_id: int) -> None:
        self._game_actors[actor_id] = actor
        actor.actor_id = actor_id

    def _remove_actor(self, actor_id: int) -> bool:
        return self._game_actors.pop(actor_id, None) is not None

    def get_actor(self, actor_id: int) -> Optional[Actor]:
        return self._game_actors.get(actor_id)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_unit_at(self, x: int, y: int) -> Optional[Unit]:
        act = self._game_actors.get(self._units[x][y])
        if act is not None:
            from tribes.actors.units.unit import Unit as UnitActor
            return act  # type: ignore[return-value]
        return None

    def get_city_in_borders(self, x: int, y: int) -> Optional[City]:
        cid = self._tile_city_id[x][y]
        if cid == -1:
            return None
        return self._game_actors.get(cid)  # type: ignore[return-value]

    def is_road(self, x: int, y: int) -> bool:
        return (self._trade_network.get_trade_network_value(x, y)
                and self._terrains[x][y] is not TERRAIN.SHALLOW_WATER
                and self._terrains[x][y] is not TERRAIN.DEEP_WATER
                and self._terrains[x][y] is not TERRAIN.CITY)

    def check_trade_network(self, x: int, y: int) -> bool:
        return self._trade_network.get_trade_network_value(x, y)

    def can_build_road_at(self, tribe_id: int, x: int, y: int) -> bool:
        if not self._tribes[tribe_id].is_visible(x, y):
            return False
        ter = self._terrains[x][y]
        if ter not in (TERRAIN.VILLAGE, TERRAIN.PLAIN, TERRAIN.FOREST):
            return False
        city_id = self._tile_city_id[x][y]
        if not (city_id == -1 or self._tribes[tribe_id].controls_city(city_id)):
            return False
        if self._trade_network.get_trade_network_value(x, y):
            return False
        # no enemy unit
        u = self._game_actors.get(self._units[x][y])
        if u is not None and u.tribe_id != tribe_id:
            return False
        return True

    def get_build_road_positions(self, tribe_id: int) -> list[Vector2d]:
        positions: list[Vector2d] = []
        for i in range(self._size):
            for j in range(self._size):
                if self.can_build_road_at(tribe_id, i, j):
                    positions.append(Vector2d(i, j))
        return positions

    def add_road(self, x: int, y: int) -> None:
        self._trade_network.set_trade_network(self, x, y, True)

    def destroy_port(self, x: int, y: int) -> None:
        self._trade_network.set_trade_network(self, x, y, False)

    def build_port(self, x: int, y: int) -> None:
        self._trade_network.set_trade_network(self, x, y, True)

    def enemy_unit_at(self, tribe_id: int, x: int, y: int) -> bool:
        if self._units[x][y] == 0:
            return False
        u = self._game_actors.get(self._units[x][y])
        return u is not None and u.tribe_id != tribe_id

    # ------------------------------------------------------------------
    # Getters / setters
    # ------------------------------------------------------------------

    def get_tribes(self) -> list[Tribe]:
        return self._tribes

    def get_tribe(self, tribe_id: int) -> Tribe:
        return self._tribes[tribe_id]

    def get_size(self) -> int:
        return self._size

    def get_active_tribe_id(self) -> int:
        return self._active_tribe_id

    def set_active_tribe_id(self, tribe_id: int) -> None:
        self._active_tribe_id = tribe_id

    def set_tribes(self, tribes: list[Tribe]) -> None:
        self._tribes = list(tribes)

    def get_terrain_at(self, x: int, y: int) -> Optional[TERRAIN]:
        return self._terrains[x][y]

    def set_terrain_at(self, x: int, y: int, t: Optional[TERRAIN]) -> None:
        self._terrains[x][y] = t

    def get_resource_at(self, x: int, y: int) -> Optional[RESOURCE]:
        return self._resources[x][y]

    def set_resource_at(self, x: int, y: int, r: Optional[RESOURCE]) -> None:
        self._resources[x][y] = r

    def get_building_at(self, x: int, y: int) -> Optional[BUILDING]:
        return self._buildings[x][y]

    def set_building_at(self, x: int, y: int, b: Optional[BUILDING]) -> None:
        self._buildings[x][y] = b

    def get_units_grid(self) -> list[list[int]]:
        return self._units

    def get_unit_id_at(self, x: int, y: int) -> int:
        return self._units[x][y]

    def get_city_id_at(self, x: int, y: int) -> int:
        return self._tile_city_id[x][y]

    def get_capital_ids(self) -> list[int]:
        return self._capital_ids

    def is_native(self) -> bool:
        return self._is_native

    def get_actor_id_counter(self) -> int:
        return self._actor_id_counter

    def get_diplomacy(self) -> Diplomacy:
        return self._diplomacy

    def get_network_tiles_at(self, x: int, y: int) -> bool:
        return self._trade_network.get_trade_network_value(x, y)
