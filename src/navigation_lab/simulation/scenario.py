from collections import deque
from dataclasses import dataclass
from random import Random

from navigation_lab.adapters.grid import Cell, GridMap, GridNavigation
from navigation_lab.adapters.simulated_motor import SimulatedMotor
from navigation_lab.core.controller import NavigationController, NavigationState
from navigation_lab.core.geometry import Vec3


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    seed: int = 7
    speed: float = 2.5
    auto_obstacles: bool = True
    obstacle_interval: float = 2.0
    obstacle_lifetime: float = 4.5
    obstacle_budget: int = 5
    demo_jam: bool = True
    jam_at: float = 3.3
    jam_duration: float = 2.5
    stuck_timeout: float = 1.25

    def __post_init__(self) -> None:
        if min(self.speed, self.obstacle_interval, self.obstacle_lifetime, self.stuck_timeout) <= 0:
            raise ValueError("speed and timeouts must be positive")
        if self.obstacle_budget < 0 or self.jam_at < 0 or self.jam_duration < 0:
            raise ValueError("budgets and jam timings must be non-negative")


class Simulation:
    FIXED_DT = 1.0 / 60.0

    def __init__(self, config: SimulationConfig | None = None) -> None:
        self.config = config or SimulationConfig()
        self.random = Random(self.config.seed)
        walls = {(4, y) for y in range(1, 13) if y not in (3, 10)}
        walls |= {(9, y) for y in range(2, 14) if y not in (6, 12)}
        walls |= {(x, 7) for x in (5, 6, 8)}
        self.grid = GridMap(15, 15, walls)
        self.backend = GridNavigation(self.grid)
        self.start = (1, 1)
        self.goal = (13, 13)
        self.motor = SimulatedMotor(
            self.backend, self.backend.center(self.start), self.config.speed
        )
        self.controller = NavigationController(
            self.backend, self.motor, stuck_timeout=self.config.stuck_timeout
        )
        self.controller.set_goal(self.backend.center(self.goal))
        self.paused = False
        self.auto_obstacles = self.config.auto_obstacles
        self.obstacles_created = 0
        self._expirations: dict[Cell, float] = {}
        self._next_obstacle = self.config.obstacle_interval
        self._jam_until = 0.0
        self._demo_jam_fired = False
        self.trail: deque[Vec3] = deque([self.motor.position], maxlen=1500)
        self.previous_route: tuple[Vec3, ...] = ()

    @property
    def time(self) -> float:
        return self.controller.time

    @property
    def arrived(self) -> bool:
        return self.controller.state == NavigationState.ARRIVED

    @property
    def protected_cells(self) -> set[Cell]:
        position = self.motor.position
        # At a cell boundary the swept-point collision model touches both cells.
        # Protect both so an edit cannot create a collider under the agent.
        touching = {
            self.backend.cell_at(Vec3(position.x + dx, position.y + dy))
            for dx in (-1e-7, 1e-7)
            for dy in (-1e-7, 1e-7)
        }
        return {self.start, self.goal, *touching}

    def toggle_obstacle(self, cell: Cell) -> None:
        if cell in self.protected_cells:
            self.controller.record("edit", "start / goal / agent cell is protected")
            return
        blocked = cell not in self.grid.obstacles
        if self.grid.set_obstacle(cell, blocked):
            # Clicking an automatic obstacle removes it; manual additions have no expiry.
            self._expirations.pop(cell, None)
            self.controller.record("obstacle" if blocked else "cleared", f"manual {cell}")

    def change_goal(self, cell: Cell) -> None:
        if self.grid.contains(cell):
            self.goal = cell
            self._expirations.pop(cell, None)
            self.controller.set_goal(self.backend.center(cell))

    def inject_jam(self, duration: float | None = None) -> None:
        if self.arrived:
            return
        duration = self.config.jam_duration if duration is None else duration
        if duration <= 0:
            return
        self._jam_until = max(self._jam_until, self.time + duration)
        self.motor.blocked = True
        self.controller.record("jam", f"motor frozen for {duration:.1f}s")

    def spawn_obstacle(self) -> bool:
        candidates = sorted(
            {
                self.backend.cell_at(point)
                for point in self.controller.waypoints
                if self.backend.cell_at(point) not in self.protected_cells
                and self.grid.contains(self.backend.cell_at(point))
            }
        )
        if not candidates:
            candidates = [
                (x, y)
                for y in range(self.grid.height)
                for x in range(self.grid.width)
                if (x, y) not in self.protected_cells and self.grid.contains((x, y))
            ]
        if not candidates or self.arrived:
            return False
        cell = self.random.choice(candidates)
        self.grid.set_obstacle(cell, True)
        self._expirations[cell] = self.time + self.config.obstacle_lifetime
        self.obstacles_created += 1
        self.controller.record("obstacle", f"temporary {cell}")
        return True

    def tick(self, dt: float = FIXED_DT) -> None:
        """Call with a fixed timestep. Pausing also pauses expiry and stuck detection."""
        if self.paused or self.arrived or dt <= 0:
            return
        now = self.time
        for cell, expiration in list(self._expirations.items()):
            if now >= expiration:
                self.grid.set_obstacle(cell, False)
                del self._expirations[cell]
                self.controller.record("cleared", f"expired {cell}")
        if (
            self.auto_obstacles
            and self.obstacles_created < self.config.obstacle_budget
            and now >= self._next_obstacle
        ):
            self.spawn_obstacle()
            self._next_obstacle = now + self.config.obstacle_interval
        if self.config.demo_jam and not self._demo_jam_fired and now >= self.config.jam_at:
            self.inject_jam()
            self._demo_jam_fired = True
        was_blocked = self.motor.blocked
        self.motor.blocked = now < self._jam_until
        if was_blocked and not self.motor.blocked:
            self.controller.record("released", "motor feedback restored")
        old_count = self.controller.plan_count
        old_route = (self.motor.position, *self.controller.waypoints)
        self.controller.tick(dt)
        if self.controller.plan_count != old_count:
            self.previous_route = old_route
        if self.motor.position.distance_to(self.trail[-1]) >= 0.12:
            self.trail.append(self.motor.position)

    def report(self) -> dict[str, object]:
        position = self.motor.position
        return {
            "seed": self.config.seed,
            "state": self.controller.state.value,
            "arrived": self.arrived,
            "simulation_seconds": round(self.time, 3),
            "position": [position.x, position.y, position.z],
            "goal": list(self.goal),
            "distance_travelled": round(self.motor.distance_travelled, 3),
            "plans": self.controller.plan_count,
            "replans": self.controller.replan_count,
            "route_invalidations": self.controller.invalidations,
            "stuck_detections": self.controller.stuck_count,
            "obstacles_created": self.obstacles_created,
            "events": [
                {"time": round(e.time, 3), "kind": e.kind, "detail": e.detail}
                for e in self.controller.events
            ],
        }
