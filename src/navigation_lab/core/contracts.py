from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from navigation_lab.core.geometry import Vec3


class SearchGraph[Node: Hashable](Protocol):
    """A* sees nodes and costs, not grid cells or polygons.

    Costs must be non-negative. Use an admissible heuristic (zero is always safe).
    """

    def contains(self, node: Node) -> bool: ...
    def neighbors(self, node: Node) -> Iterable[tuple[Node, float]]: ...
    def heuristic(self, node: Node, goal: Node) -> float: ...


@dataclass(frozen=True, slots=True)
class Route:
    waypoints: tuple[Vec3, ...]
    expanded_nodes: int = 0


class NavigationBackend(Protocol):
    @property
    def revision(self) -> int: ...

    def plan(self, start: Vec3, goal: Vec3) -> Route | None: ...
    def route_is_valid(self, position: Vec3, waypoints: Sequence[Vec3]) -> bool: ...
    def can_traverse(self, start: Vec3, end: Vec3) -> bool: ...


class MotionDriver(Protocol):
    """Position is observed feedback, not the position the controller wishes to reach."""

    @property
    def position(self) -> Vec3: ...

    def move_towards(self, target: Vec3, dt: float) -> None: ...
