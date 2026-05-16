"A*/Dijkstra pathfinder ported from Pathfinder.java."
from __future__ import annotations

import heapq
from typing import TYPE_CHECKING, Optional, Protocol

if TYPE_CHECKING:
    from tribes.utils.vector2d import Vector2d

from tribes.utils.path_node import PathNode


class NeighbourHelper(Protocol):
    """Interface for graph neighbour providers."""

    def get_neighbours(self, frm: Vector2d, cost_from: float) -> list[PathNode]:
        ...

    def add_jump_link(self, frm: Vector2d, to: Vector2d, reverse: bool) -> None:
        ...


class Pathfinder:
    """Dijkstra (find_paths) and A* (find_path_to) pathfinder."""

    def __init__(self, root_pos: Vector2d, provider: NeighbourHelper) -> None:
        self.root: PathNode = PathNode(root_pos)
        self._provider: NeighbourHelper = provider
        self.nodes: set[PathNode] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_paths(self) -> list[PathNode]:
        """Dijkstra — returns all reachable nodes."""
        return self._dijkstra()

    def find_path_to(self, goal_position: Vector2d) -> Optional[list[PathNode]]:
        """A* — returns path to goal, or None if unreachable."""
        return self._find_path(PathNode(goal_position))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calculate_path(self, node: PathNode) -> list[PathNode]:
        path: list[PathNode] = []
        cur: Optional[PathNode] = node
        while cur is not None:
            if cur.get_parent() is not None:
                path.insert(0, cur)
            cur = cur.get_parent()
        return path

    def _dijkstra(self) -> list[PathNode]:
        self.nodes = set()

        self.root.set_visited(True)
        self.root.set_total_cost(0.0)

        destinations: list[PathNode] = []
        open_list: list[PathNode] = []
        visited: set[PathNode] = set()
        visited.add(self.root)
        heapq.heappush(open_list, self.root)
        self.nodes.add(self.root)

        while open_list:
            node = heapq.heappop(open_list)

            if node is not self.root:
                destinations.append(node)

            neighbours = self._provider.get_neighbours(node.get_position(), node.get_total_cost())
            for nb in neighbours:
                nb_cost = nb.get_total_cost()

                # find in cache
                neighbour: Optional[PathNode] = None
                for n2 in self.nodes:
                    if nb == n2:
                        neighbour = n2
                        break
                if neighbour is None:
                    neighbour = nb

                if neighbour not in visited:
                    neighbour.set_visited(True)
                    visited.add(neighbour)
                    neighbour.set_total_cost(nb_cost + node.get_total_cost())
                    heapq.heappush(open_list, neighbour)
                    self.nodes.add(neighbour)
                elif nb_cost + node.get_total_cost() < neighbour.get_total_cost():
                    neighbour.set_total_cost(nb_cost + node.get_total_cost())

        return destinations

    def _find_path(self, goal: PathNode) -> Optional[list[PathNode]]:
        from tribes.utils.vector2d import Vector2d

        self.nodes = set()
        node: Optional[PathNode] = None
        open_list: list[PathNode] = []
        closed_set: set[PathNode] = set()

        self.root.set_total_cost(0.0)
        dist = Vector2d.chebychev_distance(self.root.get_position(), goal.get_position())
        self.root.set_estimated_cost(dist)
        heapq.heappush(open_list, self.root)
        self.nodes.add(self.root)

        while open_list:
            node = heapq.heappop(open_list)
            closed_set.add(node)

            if node.get_x() == goal.get_x() and node.get_y() == goal.get_y():
                return self._calculate_path(node)

            neighbours = self._provider.get_neighbours(node.get_position(), node.get_total_cost())
            for nb in neighbours:
                nb_cost = nb.get_total_cost()

                neighbour: Optional[PathNode] = None
                for n2 in self.nodes:
                    if nb == n2:
                        neighbour = n2
                        break
                if neighbour is None:
                    neighbour = nb

                if neighbour not in closed_set and not any(
                    n == neighbour for n in open_list
                ):
                    neighbour.set_total_cost(nb_cost + node.get_total_cost())
                    dist = Vector2d.chebychev_distance(
                        neighbour.get_position(), goal.get_position()
                    )
                    neighbour.set_estimated_cost(dist)
                    neighbour.set_parent(node)
                    heapq.heappush(open_list, neighbour)
                    self.nodes.add(neighbour)
                elif nb_cost + node.get_total_cost() < neighbour.get_total_cost():
                    neighbour.set_total_cost(nb_cost + node.get_total_cost())
                    neighbour.set_parent(node)
                    # re-heapify
                    if neighbour in closed_set:
                        closed_set.discard(neighbour)
                    if any(n == neighbour for n in open_list):
                        open_list = [n for n in open_list if n != neighbour]
                        heapq.heapify(open_list)
                    heapq.heappush(open_list, neighbour)

        if node is None or node.get_x() != goal.get_x() or node.get_y() != goal.get_y():
            return None
        return self._calculate_path(node)
