from collections.abc import Iterable, Sequence
from math import floor

from navigation_lab.core.astar import astar
from navigation_lab.core.contracts import Route
from navigation_lab.core.geometry import Vec3

type Cell = tuple[int, int]


class GridMap:
    """4-connected grid. All mutations increment revision; dimensions and walls are immutable."""

    def __init__(self, width: int, height: int, walls: Iterable[Cell] = ()) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("grid dimensions must be positive")
        self.width = width
        self.height = height
        self.walls = frozenset(walls)
        if any(not self.in_bounds(cell) for cell in self.walls):
            raise ValueError("wall outside grid")
        self._obstacles: set[Cell] = set()
        self.revision = 0

    @property
    def obstacles(self) -> frozenset[Cell]:
        return frozenset(self._obstacles)

    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.width and 0 <= cell[1] < self.height

    def contains(self, node: Cell) -> bool:
        return self.in_bounds(node) and node not in self.walls and node not in self._obstacles

    def set_obstacle(self, cell: Cell, blocked: bool) -> bool:
        if not self.in_bounds(cell) or cell in self.walls:
            return False
        if (cell in self._obstacles) == blocked:
            return False
        if blocked:
            self._obstacles.add(cell)
        else:
            self._obstacles.remove(cell)
        self.revision += 1
        return True

    def neighbors(self, node: Cell) -> Iterable[tuple[Cell, float]]:
        x, y = node
        for neighbor in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
            if self.contains(neighbor):
                yield neighbor, 1.0

    def heuristic(self, node: Cell, goal: Cell) -> float:
        return float(abs(node[0] - goal[0]) + abs(node[1] - goal[1]))


class GridNavigation:
    def __init__(self, grid: GridMap) -> None:
        self.grid = grid

    @property
    def revision(self) -> int:
        return self.grid.revision

    @staticmethod
    def cell_at(position: Vec3) -> Cell:
        return floor(position.x + 0.5), floor(position.y + 0.5)

    @staticmethod
    def center(cell: Cell) -> Vec3:
        return Vec3(float(cell[0]), float(cell[1]))

    def plan(self, start: Vec3, goal: Vec3) -> Route | None:
        if abs(start.z) > 1e-8 or abs(goal.z) > 1e-8:
            return None
        result = astar(self.grid, self.cell_at(start), self.cell_at(goal))
        if result is None:
            return None
        # Reconnect a continuous mid-edge position to its cell center before following new edges.
        points = tuple(self.center(cell) for cell in result.nodes)
        if points[-1].distance_to(goal) > 1e-8:
            points += (goal,)
        if not self.route_is_valid(start, points):
            return None
        return Route(points, result.expanded_nodes)

    def route_is_valid(self, position: Vec3, waypoints: Sequence[Vec3]) -> bool:
        for point in waypoints:
            if not self.can_traverse(position, point):
                return False
            position = point
        return True

    def can_traverse(self, start: Vec3, end: Vec3) -> bool:
        if abs(start.z) > 1e-8 or abs(end.z) > 1e-8:
            return False
        if not self.grid.contains(self.cell_at(start)) or not self.grid.contains(self.cell_at(end)):
            return False
        # Swept point versus blocked cell rectangles: even a large time step cannot tunnel.
        for x, y in self.grid.walls | self.grid.obstacles:
            low, high = 0.0, 1.0
            for origin, delta, minimum, maximum in (
                (start.x, end.x - start.x, x - 0.5, x + 0.5),
                (start.y, end.y - start.y, y - 0.5, y + 0.5),
            ):
                if abs(delta) < 1e-12:
                    if not minimum <= origin <= maximum:
                        low, high = 1.0, 0.0
                        break
                else:
                    a, b = (minimum - origin) / delta, (maximum - origin) / delta
                    low, high = max(low, min(a, b)), min(high, max(a, b))
            if low <= high:
                return False
        return True
