from collections.abc import Hashable
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from math import inf

from navigation_lab.core.contracts import SearchGraph


@dataclass(frozen=True, slots=True)
class SearchResult[Node]:
    nodes: tuple[Node, ...]
    cost: float
    expanded_nodes: int


def astar[Node: Hashable](
    graph: SearchGraph[Node], start: Node, goal: Node
) -> SearchResult[Node] | None:
    """Return an optimal route, or None. Ties never compare arbitrary node objects."""
    if not graph.contains(start) or not graph.contains(goal):
        return None
    serial = count()
    frontier = [(graph.heuristic(start, goal), next(serial), 0.0, start)]
    costs = {start: 0.0}
    parents: dict[Node, Node] = {}
    expanded = 0
    while frontier:
        _, _, cost, node = heappop(frontier)
        if cost > costs[node]:
            continue
        expanded += 1
        if node == goal:
            path = [node]
            while node in parents:
                node = parents[node]
                path.append(node)
            return SearchResult(tuple(reversed(path)), cost, expanded)
        for neighbor, step_cost in graph.neighbors(node):
            if step_cost < 0:
                raise ValueError("A* requires non-negative edge costs")
            candidate = cost + step_cost
            if candidate < costs.get(neighbor, inf):
                parents[neighbor] = node
                costs[neighbor] = candidate
                heappush(
                    frontier,
                    (
                        candidate + graph.heuristic(neighbor, goal),
                        next(serial),
                        candidate,
                        neighbor,
                    ),
                )
    return None
