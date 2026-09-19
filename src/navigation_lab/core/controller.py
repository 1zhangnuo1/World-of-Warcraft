from collections import deque
from dataclasses import dataclass
from enum import StrEnum

from navigation_lab.core.contracts import MotionDriver, NavigationBackend
from navigation_lab.core.geometry import Vec3
from navigation_lab.core.stuck import StuckDetector


class NavigationState(StrEnum):
    IDLE = "idle"
    MOVING = "moving"
    RECOVERING = "recovering"
    WAITING = "waiting"
    ARRIVED = "arrived"


@dataclass(frozen=True, slots=True)
class NavigationEvent:
    time: float
    kind: str
    detail: str


class NavigationController:
    """Plan → command movement → observe feedback → recover, without knowing the renderer."""

    def __init__(
        self,
        backend: NavigationBackend,
        motor: MotionDriver,
        *,
        stuck_timeout: float = 1.25,
        retry_interval: float = 0.75,
    ) -> None:
        if stuck_timeout <= 0 or retry_interval <= 0:
            raise ValueError("timeouts must be positive")
        self.backend = backend
        self.motor = motor
        self.detector = StuckDetector(timeout=stuck_timeout)
        self.retry_interval = retry_interval
        self.state = NavigationState.IDLE
        self.goal: Vec3 | None = None
        self.waypoints: deque[Vec3] = deque()
        self.events: deque[NavigationEvent] = deque(maxlen=80)
        self.time = 0.0
        self.plan_count = 0
        self.stuck_count = 0
        self.invalidations = 0
        self.expanded_nodes = 0
        self.last_reason = "-"
        self._known_revision = backend.revision
        self._retry_at = 0.0

    @property
    def replan_count(self) -> int:
        return max(0, self.plan_count - 1)

    def record(self, kind: str, detail: str) -> None:
        self.events.append(NavigationEvent(self.time, kind, detail))

    def set_goal(self, goal: Vec3) -> None:
        self.goal = goal
        self.detector.reset(self.motor.position)
        self._plan("new goal")

    def _plan(self, reason: str) -> None:
        if self.goal is None:
            return
        self.plan_count += 1
        self.last_reason = reason
        self._known_revision = self.backend.revision
        route = self.backend.plan(self.motor.position, self.goal)
        self.waypoints.clear()
        if route is None:
            self.expanded_nodes = 0
            self.state = NavigationState.WAITING
            self._retry_at = self.time + self.retry_interval
            self.record("no_path", reason)
            return
        self.expanded_nodes = route.expanded_nodes
        self.waypoints.extend(route.waypoints)
        self._consume_reached()
        self.state = NavigationState.RECOVERING if reason == "stuck" else NavigationState.MOVING
        self.record("plan", f"{reason} / {len(self.waypoints)} waypoints")
        self._check_arrival()

    def _consume_reached(self) -> None:
        while self.waypoints and self.motor.position.distance_to(self.waypoints[0]) < 1e-6:
            self.waypoints.popleft()

    def _check_arrival(self) -> None:
        if self.goal is not None and self.motor.position.distance_to(self.goal) < 1e-6:
            self.state = NavigationState.ARRIVED
            self.waypoints.clear()
            self.detector.reset(self.motor.position)
            self.record("arrived", "actual position reached goal")

    def tick(self, dt: float) -> None:
        if dt <= 0:
            return
        self.time += dt
        if self.state in (NavigationState.IDLE, NavigationState.ARRIVED):
            return
        changed = self.backend.revision != self._known_revision
        if self.state == NavigationState.WAITING:
            self.detector.reset(self.motor.position)
            if changed or self.time >= self._retry_at:
                self._plan("map changed" if changed else "retry")
            return
        if changed:
            self._known_revision = self.backend.revision
            if not self.backend.route_is_valid(self.motor.position, tuple(self.waypoints)):
                self.invalidations += 1
                self.record("invalidated", "remaining route blocked")
                # Do not reset displacement tracking: frequent map edits must not hide a stall.
                self._plan("route blocked")
        if self.state in (NavigationState.WAITING, NavigationState.ARRIVED):
            return
        self._consume_reached()
        before = self.motor.position
        if self.waypoints:
            self.motor.move_towards(self.waypoints[0], dt)
        self._consume_reached()
        self._check_arrival()
        if self.state == NavigationState.ARRIVED:
            return
        if before.distance_to(self.motor.position) > 1e-8:
            self.state = NavigationState.MOVING
        if self.detector.observe(self.motor.position, dt, expected_to_move=True):
            self.stuck_count += 1
            self.record("stuck", f"no effective displacement for {self.detector.stalled_for:.2f}s")
            self.detector.reset(self.motor.position)
            self._plan("stuck")
