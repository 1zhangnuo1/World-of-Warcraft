from collections import deque
from dataclasses import dataclass
from random import Random

import pytest

from navigation_lab.adapters.grid import Cell, GridMap
from navigation_lab.core.astar import astar


def bfs_length(grid: GridMap, start: Cell, goal: Cell) -> int | None:
    queue = deque([(start, 0)])
    visited = {start}
    while queue:
        node, distance = queue.popleft()
        if node == goal:
            return distance
        for neighbor, _ in grid.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    return None


@pytest.mark.parametrize("seed", range(20))
def test_astar_matches_independent_bfs(seed: int) -> None:
    rng = Random(seed)
    walls = {
        (x, y)
        for x in range(10)
        for y in range(10)
        if rng.random() < 0.27 and (x, y) not in ((0, 0), (9, 9))
    }
    grid = GridMap(10, 10, walls)
    actual = astar(grid, (0, 0), (9, 9))
    expected = bfs_length(grid, (0, 0), (9, 9))
    if expected is None:
        assert actual is None
    else:
        assert actual is not None
        assert actual.cost == expected
        assert actual.nodes[0] == (0, 0) and actual.nodes[-1] == (9, 9)
        assert all(grid.contains(cell) for cell in actual.nodes)
        assert all(
            grid.heuristic(a, b) == 1 for a, b in zip(actual.nodes, actual.nodes[1:], strict=False)
        )


def test_invalid_endpoints_and_same_position() -> None:
    grid = GridMap(3, 3, [(1, 1)])
    assert astar(grid, (0, 0), (1, 1)) is None
    assert astar(grid, (-1, 0), (2, 2)) is None
    result = astar(grid, (0, 0), (0, 0))
    assert result is not None and result.nodes == ((0, 0),) and result.cost == 0


@dataclass(frozen=True)
class Polygon:
    name: str


def test_weighted_non_grid_nodes_do_not_need_ordering() -> None:
    s, a, b, g = (Polygon(n) for n in "sabg")

    class PolygonGraph:
        edges = {s: [(a, 1.0), (b, 1.0)], a: [(g, 9.0)], b: [(g, 2.0)], g: []}

        def contains(self, node: Polygon) -> bool:
            return node in self.edges

        def neighbors(self, node: Polygon) -> list[tuple[Polygon, float]]:
            return self.edges[node]

        def heuristic(self, node: Polygon, goal: Polygon) -> float:
            return 0.0

    result = astar(PolygonGraph(), s, g)
    assert result is not None
    assert result.nodes == (s, b, g)
    assert result.cost == 3
