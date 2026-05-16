"GameState, ported from GameState.java."
from __future__ import annotations

import logging
import random as _random
from typing import TYPE_CHECKING, Optional

from tribes.types import ACTION, GAME_MODE, RESULT, TURN_STATUS
from tribes import config as cfg

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.board import Board
    from tribes.game.tribe_result import TribeResult
    from tribes.actors.tribe import Tribe
    from tribes.actors.city import City
    from tribes.actors.units.unit import Unit
    from tribes.actions.action import Action


class GameState:
    """Master game state object."""

    def __init__(self, rnd: _random.Random, game_mode: GAME_MODE) -> None:
        self._rnd = rnd
        self._game_mode = game_mode
        self._tick: int = 0
        self._board: Optional[Board] = None
        self._can_end_turn: list[bool] = []
        self._city_actions: dict[int, list[Action]] = {}
        self._unit_actions: dict[int, list[Action]] = {}
        self._tribe_actions: list[Action] = []
        self._turn_must_end: bool = False
        self._game_is_over: bool = False
        self._computed_action_tribe_id_flag: int = -1
        self._leveling_up: bool = False
        self._ranking: list[TribeResult] = []

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def init(self, filename: str) -> None:
        with open(filename, "r") as f:
            lines = [line.rstrip("\n") for line in f.readlines()]
        self._init_game_state(lines)

    def init_from_lines(self, lines: list[str]) -> None:
        self._init_game_state(lines)

    def _init_game_state(self, lines: list[str]) -> None:
        from tribes.game.level_loader import LevelLoader
        ll = LevelLoader()
        self._board = ll.build_level(lines, self._rnd)

        tribes = self._board.get_tribes()
        for tribe in tribes:
            start_city_id = tribe.get_cities_id()[0]
            c: City = self._board.get_actor(start_city_id)
            city_pos = c.get_position()
            tribe.clear_view(city_pos.x, city_pos.y,
                             cfg.FIRST_CITY_CLEAR_RANGE, self._rnd, self._board)

        self._can_end_turn = [False] * len(tribes)

    # ------------------------------------------------------------------
    # Action computation
    # ------------------------------------------------------------------

    def compute_player_actions(self, tribe: Tribe) -> None:
        from tribes.actions.city_actions.builders.city_action_builder import CityActionBuilder
        from tribes.actions.unit_actions.builders.unit_action_builder import UnitActionBuilder
        from tribes.actions.tribe_actions.builders.tribe_action_builder import TribeActionBuilder

        self._board.set_active_tribe_id(tribe.tribe_id)

        if (self._computed_action_tribe_id_flag != -1
                and self._computed_action_tribe_id_flag == tribe.tribe_id):
            return  # already computed

        self._computed_action_tribe_id_flag = tribe.tribe_id
        self._city_actions = {}
        self._unit_actions = {}
        self._tribe_actions = []

        if self._game_is_over:
            return

        cities = tribe.get_cities_id()
        all_units: list[int] = []
        cab = CityActionBuilder()

        num_cities = len(cities)
        i = 0
        self._leveling_up = False

        while not self._leveling_up and i < num_cities:
            city_id = cities[i]
            c: City = self._board.get_actor(city_id)
            actions = cab.get_actions(self, c)
            self._leveling_up = cab.city_levels_up()

            if len(actions) > 0:
                if self._leveling_up:
                    self._city_actions.clear()
                self._city_actions[city_id] = actions

            if not self._leveling_up:
                unit_ids = c.get_units_id()
                all_units.extend(unit_ids)
                i += 1

        active_tribe_id = self._board.get_active_tribe_id()
        if self._leveling_up:
            self._can_end_turn[active_tribe_id] = False
            return
        else:
            self._can_end_turn[active_tribe_id] = True

        all_units.extend(tribe.get_extra_units())

        uab = UnitActionBuilder()
        for unit_id in all_units:
            u: Unit = self._board.get_actor(unit_id)
            if u is None:
                continue
            actions = uab.get_actions(self, u)
            if len(actions) > 0:
                self._unit_actions[unit_id] = actions

        tab = TribeActionBuilder()
        actions = tab.get_actions(self, tribe)
        self._tribe_actions.extend(actions)

    def exist_available_actions(self, tribe: Tribe) -> bool:
        tribe_id = tribe.tribe_id
        if self._board.get_active_tribe_id() != tribe_id:
            return False
        n_actions = 0
        for city_id in self._city_actions:
            n_actions += len(self._city_actions[city_id])
            if n_actions > 0:
                return True
        for unit_id in self._unit_actions:
            n_actions += len(self._unit_actions[unit_id])
            if n_actions > 0:
                return True
        if (len(self._tribe_actions) == 1
                and self._tribe_actions[0].get_action_type() is ACTION.END_TURN):
            return False
        return True

    # ------------------------------------------------------------------
    # Advance
    # ------------------------------------------------------------------

    def next(self, action: Optional[Action]) -> None:
        """Execute action without computing next actions."""
        if action is not None:
            executed = action.execute(self)
            if not executed:
                logger.debug(f"Tick {self._tick}: action [{action}] couldn't execute")
            self._computed_action_tribe_id_flag = -1

    def advance(self, action: Optional[Action], compute_actions: bool) -> None:
        """Execute action and optionally compute next player's actions."""
        if action is not None:
            executed = action.execute(self)
            if not executed:
                logger.debug(f"FM: Action [{action}] couldn't execute")

            if executed:
                if action.get_action_type() is ACTION.END_TURN:
                    self.end_turn(self.get_active_tribe())
                    self.game_over()

                    if not self._game_is_over:
                        cur_id = self._board.get_active_tribe_id()
                        player_found = False
                        while not player_found:
                            cur_id = (cur_id + 1) % len(self._can_end_turn)
                            if self._board.get_tribe(cur_id).get_winner() is not RESULT.LOSS:
                                player_found = True
                            if cur_id == self._board.get_active_tribe_id():
                                logger.error(
                                    f"ForwardModel ERROR: all players but {self._board.get_active_tribe_id()} "
                                    f"lost, but not game over?")
                                self.game_over()
                                break

                        self._board.set_active_tribe_id(cur_id)
                        self.init_turn(self.get_active_tribe())

                self._computed_action_tribe_id_flag = -1
                if compute_actions:
                    self.compute_player_actions(self.get_active_tribe())

    # ------------------------------------------------------------------
    # End turn / init turn
    # ------------------------------------------------------------------

    def end_turn(self, tribe: Tribe) -> None:
        from tribes.actions.unit_actions.builders.recover_factory import RecoverFactory

        all_tribe_units: list[int] = []
        for city_id in tribe.get_cities_id():
            city: City = self.get_actor(city_id)
            all_tribe_units.extend(city.get_units_id())

        all_tribe_units.extend(tribe.get_extra_units())
        for unit_id in all_tribe_units:
            unit: Unit = self.get_actor(unit_id)
            if unit is None:
                continue
            if unit.get_status() is TURN_STATUS.FRESH:
                recover_actions = RecoverFactory().compute_action_variants(unit, self)
                if len(recover_actions) > 0:
                    recover_actions[0].execute(self)

    def init_turn(self, tribe: Tribe) -> None:
        tribe_cities = tribe.get_cities_id()
        all_tribe_units: list[int] = []
        self.set_end_turn(False)

        acum_prod = 0
        for city_id in tribe_cities:
            city: City = self.get_actor(city_id)
            produces = True
            city_pos = city.get_position()
            unit_id_at = self._board.get_unit_id_at(city_pos.x, city_pos.y)
            if unit_id_at > 0:
                u: Unit = self.get_actor(unit_id_at)
                produces = (u.tribe_id == tribe.tribe_id)

            if produces:
                acum_prod += city.get_production()

            all_tribe_units.extend(city.get_units_id())

            for b in city.get_buildings():
                if b.type.is_temple():
                    temple_points = b.new_turn()
                    tribe.add_score(temple_points)
                    city.add_points_worth(temple_points)

        if self._tick == 0:
            tribe.set_stars(cfg.INITIAL_STARS)
        else:
            acum_prod = max(0, acum_prod)
            tribe.add_stars(acum_prod)

        all_tribe_units.extend(tribe.get_extra_units())
        for unit_id in all_tribe_units:
            unit: Unit = self.get_actor(unit_id)
            if unit is None:
                continue
            if unit.get_status() is TURN_STATUS.PUSHED:
                unit.set_status(TURN_STATUS.MOVED)
            else:
                unit.set_status(TURN_STATUS.FRESH)

        tribe.add_pacifist_count()
        tribe.reset_stars_sent()
        tribe.set_has_declared_war(False)

    # ------------------------------------------------------------------
    # Push / Kill
    # ------------------------------------------------------------------

    def push_unit(self, to_push: Unit, start_x: int, start_y: int) -> None:
        tribe = self.get_tribe(to_push.tribe_id)
        pushed = self._board.push_unit(tribe, to_push, start_x, start_y, self._rnd)
        if not pushed:
            self.kill_unit(to_push)

    def kill_unit(self, to_kill: Unit) -> None:
        self._board.remove_unit_from_board(to_kill)
        c: City = self.get_actor(to_kill.get_city_id())
        tribe = self.get_tribe(to_kill.tribe_id)
        self._board.remove_unit_from_city(to_kill, c, tribe)
        tribe.subtract_score(to_kill.get_type().get_points())

    # ------------------------------------------------------------------
    # Game over
    # ------------------------------------------------------------------

    def game_over(self) -> bool:
        max_turns = self._game_mode.get_max_turns()
        is_ended = False
        capitals = self._board.get_capital_ids()

        if self._game_mode is GAME_MODE.CAPITALS:
            for i in range(len(self._can_end_turn)):
                t = self._board.get_tribe(i)
                if t.get_winner() is RESULT.LOSS:
                    continue
                winner = True
                for cap in capitals:
                    if not t.controls_city(cap):
                        winner = False
                        break
                if winner:
                    is_ended = True
                    self._board.get_tribe(i).set_winner(RESULT.WIN)
                    break

        self.compute_game_ranking()

        if self._game_mode is GAME_MODE.SCORE:
            num_non_loss = sum(
                1 for tr in self._ranking
                if self.get_tribe(tr.get_id()).get_winner() is not RESULT.LOSS
            )
            is_ended = num_non_loss <= 1

        if is_ended or self._tick > max_turns:
            first = True
            for tr in self._ranking:
                tribe_id = tr.get_id()
                res = RESULT.WIN if first else RESULT.LOSS
                self._board.get_tribe(tribe_id).set_winner(res)
                tr.set_result(res)
                first = False
            is_ended = True

        self._game_is_over = is_ended
        return is_ended

    def compute_game_ranking(self) -> None:
        from tribes.game.tribe_result import TribeResult
        self._ranking = []
        for i in range(len(self._can_end_turn)):
            t = self._board.get_tribe(i)
            tr = TribeResult(
                i, t.get_winner(), t.get_score(),
                t.get_tech_tree().get_num_researched(),
                t.get_num_cities(),
                t.get_max_production(self),
                t.get_n_wars_declared(),
                t.get_n_stars_sent()
            )
            self._ranking.append(tr)
        self._ranking.sort()

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    def copy(self, player_idx: int = -1) -> GameState:
        gs_copy = GameState(self._rnd, self._game_mode)
        gs_copy._board = self._board.copy(player_idx != -1, player_idx)
        gs_copy._tick = self._tick
        gs_copy._turn_must_end = self._turn_must_end
        gs_copy._game_is_over = self._game_is_over

        gs_copy._can_end_turn = list(self._can_end_turn)
        gs_copy._leveling_up = self._leveling_up

        gs_copy._tribe_actions = [a.copy() for a in self._tribe_actions]

        gs_copy._unit_actions = {}
        for unit_id, actions in self._unit_actions.items():
            gs_copy._unit_actions[unit_id] = [a.copy() for a in actions]

        gs_copy._city_actions = {}
        for city_id, actions in self._city_actions.items():
            gs_copy._city_actions[city_id] = [a.copy() for a in actions]

        gs_copy._ranking = [tr.copy() for tr in self._ranking]

        return gs_copy

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_actor(self, actor_id: int):
        return self._board.get_actor(actor_id)

    def get_tick(self) -> int:
        return self._tick

    def inc_tick(self) -> None:
        self._tick += 1

    def get_board(self) -> Board:
        return self._board

    def get_tribes(self) -> list[Tribe]:
        return self._board.get_tribes()

    def get_tribe(self, tribe_id: int) -> Tribe:
        return self._board.get_tribe(tribe_id)

    def get_active_tribe(self) -> Optional[Tribe]:
        active_id = self._board.get_active_tribe_id()
        if active_id != -1:
            return self._board.get_tribe(active_id)
        return None

    def get_active_tribe_id(self) -> int:
        return self._board.get_active_tribe_id()

    def get_random_generator(self) -> _random.Random:
        return self._rnd

    def is_native(self) -> bool:
        return self._board.is_native()

    def is_game_over(self) -> bool:
        return self._game_is_over

    def set_game_is_over(self, val: bool) -> None:
        self._game_is_over = val

    def is_leveling_up(self) -> bool:
        return self._leveling_up

    def can_end_turn(self, tribe_id: int) -> bool:
        return self._can_end_turn[tribe_id]

    def set_end_turn(self, end_turn: bool) -> None:
        self._turn_must_end = end_turn

    def is_turn_ending(self) -> bool:
        return self._turn_must_end

    def get_city_actions(self, city_id_or_city=None) -> dict | list:
        if city_id_or_city is None:
            return self._city_actions
        if hasattr(city_id_or_city, "actor_id"):
            return self._city_actions.get(city_id_or_city.actor_id, [])
        return self._city_actions.get(city_id_or_city, [])

    def get_unit_actions(self, unit_id_or_unit=None) -> dict | list:
        if unit_id_or_unit is None:
            return self._unit_actions
        if hasattr(unit_id_or_unit, "actor_id"):
            return self._unit_actions.get(unit_id_or_unit.actor_id, [])
        return self._unit_actions.get(unit_id_or_unit, [])

    def get_tribe_actions(self) -> list[Action]:
        return self._tribe_actions

    def get_all_available_actions(self) -> list[Action]:
        all_actions: list[Action] = list(self._tribe_actions)
        for city_id in self._city_actions:
            all_actions.extend(self._city_actions[city_id])
        for unit_id in self._unit_actions:
            all_actions.extend(self._unit_actions[unit_id])
        return all_actions

    def get_all_city_actions(self) -> list[Action]:
        all_actions: list[Action] = []
        for city_id in self._city_actions:
            all_actions.extend(self._city_actions[city_id])
        return all_actions

    def get_all_unit_actions(self) -> list[Action]:
        all_actions: list[Action] = []
        for unit_id in self._unit_actions:
            all_actions.extend(self._unit_actions[unit_id])
        return all_actions

    def get_current_ranking(self) -> list[TribeResult]:
        return self._ranking

    def get_game_mode(self) -> GAME_MODE:
        return self._game_mode

    def get_tribe_win_status(self, player_id: int) -> RESULT:
        return self.get_tribe(player_id).get_winner()

    def get_visibility_map(self) -> list[list[bool]]:
        return self.get_active_tribe().get_obs_grid()

    def get_tribes_met(self) -> list[int]:
        return self.get_active_tribe().get_tribes_met()

    def get_cities(self, player_id: int) -> list[City]:
        cities = []
        for city_id in self.get_tribe(player_id).get_cities_id():
            cities.append(self._board.get_actor(city_id))
        return cities

    def get_units(self, player_id: int) -> list[Unit]:
        units = []
        for city_id in self.get_tribe(player_id).get_cities_id():
            city: City = self._board.get_actor(city_id)
            for unit_id in city.get_units_id():
                units.append(self._board.get_actor(unit_id))
        for unit_id in self.get_tribe(player_id).get_extra_units():
            units.append(self._board.get_actor(unit_id))
        return units

    def get_score(self, player_id: int) -> int:
        return self.get_tribe(player_id).get_score()

    def get_n_kills(self, player_id: int) -> int:
        return self.get_tribe(player_id).get_n_kills()
