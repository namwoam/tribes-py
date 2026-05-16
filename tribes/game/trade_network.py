"TradeNetwork — road/port/city connectivity grid, ported from TradeNetwork.java."

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tribes.utils.path_node import PathNode
from tribes.utils.pathfinder import Pathfinder
from tribes.utils.vector2d import Vector2d
from tribes import config as cfg
from tribes.types import TERRAIN, BUILDING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tribes.game.board import Board
    from tribes.actors.tribe import Tribe


# ---------------------------------------------------------------------------
# NeighbourHelper implementations (inner-class equivalents)
# ---------------------------------------------------------------------------


class _TradeWaterStep:
    """Pathfinder helper for water navigation between ports."""

    def __init__(self, navigable: list[list[bool]], size: int) -> None:
        self._navigable = navigable
        self._size = size

    def get_neighbours(self, frm: Vector2d, cost_from: float) -> list[PathNode]:
        neighbours: list[PathNode] = []
        step_cost = 1.0
        for tile in frm.neighborhood(1, 0, self._size):
            x, y = tile.x, tile.y
            if (
                self._navigable[x][y]
                and cost_from + step_cost <= cfg.PORT_TRADE_DISTANCE
            ):
                neighbours.append(PathNode(Vector2d(x, y), step_cost))
        return neighbours

    def add_jump_link(self, frm: Vector2d, to: Vector2d, reverse: bool) -> None:
        pass  # no jump links in water step


class _TradeNetworkStep:
    """Pathfinder helper for city road/port connectivity."""

    def __init__(self, connected: list[list[bool]]) -> None:
        self._connected = connected
        self._jump_links: dict[Vector2d, list[Vector2d]] = {}

    def get_neighbours(self, frm: Vector2d, cost_from: float) -> list[PathNode]:
        neighbours: list[PathNode] = []
        step_cost = 1.0
        size = len(self._connected)
        for tile in frm.neighborhood(1, 0, size):
            x, y = tile.x, tile.y
            if self._connected[x][y]:
                neighbours.append(PathNode(Vector2d(x, y), step_cost))
        # jump links
        if frm in self._jump_links:
            for to in self._jump_links[frm]:
                neighbours.append(PathNode(Vector2d(to.x, to.y), step_cost))
        return neighbours

    def add_jump_link(self, frm: Vector2d, to: Vector2d, reverse: bool) -> None:
        self._add_a_to_b(frm, to)
        if reverse:
            self._add_a_to_b(to, frm)

    def _add_a_to_b(self, frm: Vector2d, to: Vector2d) -> None:
        if frm not in self._jump_links:
            self._jump_links[frm] = []
        self._jump_links[frm].append(Vector2d(to.x, to.y))


# ---------------------------------------------------------------------------
# TradeNetwork
# ---------------------------------------------------------------------------


class TradeNetwork:
    """Tracks which tiles belong to the trade network (roads, ports, cities)."""

    def __init__(self, size_or_grid) -> None:
        if isinstance(size_or_grid, int):
            size = size_or_grid
            self._size = size
            self._network_tiles: list[list[bool]] = [
                [False] * size for _ in range(size)
            ]
        else:
            grid: list[list[bool]] = size_or_grid
            self._size = len(grid)
            self._network_tiles = [list(row) for row in grid]

    def set_trade_network(self, board: Board, x: int, y: int, trade: bool) -> None:
        self._network_tiles[x][y] = trade
        self._compute_trade_network(board)

    def set_trade_network_value(self, x: int, y: int, trade: bool) -> None:
        self._network_tiles[x][y] = trade

    def get_trade_network_value(self, x: int, y: int) -> bool:
        return self._network_tiles[x][y]

    def _compute_trade_network(self, board: Board) -> None:
        tribes = board.get_tribes()
        for tribe in tribes:
            self.compute_trade_network_tribe(board, tribe)

    def compute_trade_network_tribe(self, board: Board, tribe: Tribe) -> None:
        """Recompute connectivity for the given tribe."""
        # Only update for all tribes if board is native, or for the active tribe's turn
        if tribe.tribe_id != board.get_active_tribe_id() and not board.is_native():
            return

        if not tribe.controls_capital():
            tribe.update_network(
                None, board, tribe.tribe_id == board.get_active_tribe_id()
            )
            return

        n = self._size
        connected_tiles: list[list[bool]] = [[False] * n for _ in range(n)]
        navigable: list[list[bool]] = [[False] * n for _ in range(n)]
        ports: list[Vector2d] = []

        for i in range(n):
            for j in range(n):
                city_id = board.get_city_id_at(i, j)
                my_city = tribe.controls_city(city_id)
                not_enemy = my_city or city_id == -1

                ter = board.get_terrain_at(i, j)
                build = board.get_building_at(i, j)

                if my_city and (ter is TERRAIN.CITY or build is BUILDING.PORT):
                    connected_tiles[i][j] = self._network_tiles[i][j]
                    if build is BUILDING.PORT:
                        ports.append(Vector2d(i, j))
                elif not_enemy and board.is_road(i, j):
                    connected_tiles[i][j] = self._network_tiles[i][j]

                if (
                    ter in (TERRAIN.SHALLOW_WATER, TERRAIN.DEEP_WATER)
                    and tribe.is_visible(i, j)
                    and not_enemy
                ):
                    navigable[i][j] = True

        tns = _TradeNetworkStep(connected_tiles)

        # Add jump links between pairs of ports
        n_ports = len(ports)
        for i in range(n_ports - 1):
            for j in range(i + 1, n_ports):
                port_from = ports[i]
                port_to = ports[j]
                origin_pos = Vector2d(port_from.x, port_from.y)
                tp = Pathfinder(origin_pos, _TradeWaterStep(navigable, n))
                path = tp.find_path_to(Vector2d(port_to.x, port_to.y))
                if path is not None:
                    tns.add_jump_link(port_from, port_to, True)

        capital = board.get_actor(tribe.get_capital_id())
        pf = Pathfinder(capital.get_position(), tns)
        tribe.update_network(pf, board, tribe.tribe_id == board.get_active_tribe_id())
