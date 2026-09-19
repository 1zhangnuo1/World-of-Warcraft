from collections.abc import Sequence

import pytest

from navigation_lab.adapters.grid import GridMap, GridNavigation
from navigation_lab.adapters.simulated_motor import SimulatedMotor
from navigation_lab.core.contracts import Route
from navigation_lab.core.controller import NavigationController, NavigationState
from navigation_lab.core.geometry import Vec3
from navigation_lab.core.stuck import StuckDetector


def make_navigation(
    grid: GridMap, start: Vec3, goal: Vec3
) -> tuple[GridNavigation, SimulatedMotor, NavigationController]:
    backend = GridNavigation(grid)
    motor = SimulatedMotor(backend, start)
    controller = NavigationController(backend, motor)
    controller.set_goal(goal)
    return backend, motor, controller


def run_until_arrival(controller: NavigationController, seconds: float = 20.0) -> None:
    for _ in range(int(seconds * 60)):
        if controller.state == NavigationState.ARRIVED:
            break
        controller.tick(1 / 60)
    assert controller.state == NavigationState.ARRIVED


def test_continuous_motion_and_mid_edge_replanning_without_teleport() -> None:
    grid = GridMap(5, 3)
    backend, motor, controller = make_navigation(grid, Vec3(0, 1), Vec3(4, 1))
    controller.tick(0.1)
    assert motor.position == Vec3(0.25, 1)
    grid.set_obstacle((1, 1), True)
    before = motor.position
    controller.tick(1 / 60)
    assert 0 < motor.position.distance_to(before) <= motor.speed / 60 + 1e-9
    assert backend.can_traverse(before, motor.position)
    assert controller.invalidations == 1
    for _ in range(600):
        before = motor.position
        controller.tick(1 / 60)
        assert backend.can_traverse(before, motor.position)
        assert grid.contains(backend.cell_at(motor.position))
        if controller.state == NavigationState.ARRIVED:
            break
    assert motor.position.distance_to(Vec3(4, 1)) < 1e-6


def test_sealed_goal_waits_without_false_stalls_then_resumes_on_edit() -> None:
    grid = GridMap(3, 1)
    grid.set_obstacle((1, 0), True)
    _, motor, controller = make_navigation(grid, Vec3(0, 0), Vec3(2, 0))
    for _ in range(180):
        controller.tick(1 / 60)
    assert controller.state == NavigationState.WAITING
    assert controller.stuck_count == 0
    assert 3 <= controller.plan_count <= 5  # Retrying is throttled, not every frame.
    assert motor.position == Vec3(0, 0)
    grid.set_obstacle((1, 0), False)
    controller.tick(1 / 60)
    assert controller.state == NavigationState.MOVING
    run_until_arrival(controller)


def test_jam_replans_without_claiming_arrival_and_moves_after_release() -> None:
    _, motor, controller = make_navigation(GridMap(5, 1), Vec3(0, 0), Vec3(4, 0))
    motor.blocked = True
    for _ in range(100):
        controller.tick(1 / 60)
    assert controller.stuck_count == 1
    assert controller.replan_count == 1
    assert controller.state == NavigationState.RECOVERING
    assert motor.position == Vec3(0, 0)
    motor.blocked = False
    run_until_arrival(controller)
    assert motor.distance_travelled == pytest.approx(4)


def test_map_replans_do_not_mask_stuck_detection() -> None:
    grid = GridMap(6, 4)
    _, motor, controller = make_navigation(grid, Vec3(0, 0), Vec3(5, 0))
    motor.blocked = True
    for step in range(100):
        if step % 20 == 0:
            grid.set_obstacle((3, 0), (3, 0) not in grid.obstacles)
        controller.tick(1 / 60)
    assert controller.stuck_count >= 1


def test_motor_swept_collision_prevents_tunneling_and_corner_cutting() -> None:
    backend = GridNavigation(GridMap(5, 3, [(2, 1)]))
    motor = SimulatedMotor(backend, Vec3(0, 1), speed=100)
    motor.move_towards(Vec3(4, 1), 1)
    assert motor.position == Vec3(0, 1)
    assert not backend.can_traverse(Vec3(1, 1), Vec3(2, 0))
    assert not backend.can_traverse(Vec3(0, 1), Vec3(-1, 1))


def test_stuck_detector_ignores_noise_and_resets_for_waiting() -> None:
    detector = StuckDetector(timeout=1.0, minimum_displacement=0.06)
    detector.reset(Vec3(0, 0))
    for i in range(9):
        assert not detector.observe(Vec3(0.001 * (i % 2), 0), 0.1, True)
    assert detector.observe(Vec3(0, 0), 0.11, True)
    assert not detector.observe(Vec3(0, 0), 20, False)
    assert detector.stalled_for == 0


def test_already_at_goal_and_goal_changed_after_arrival() -> None:
    _, motor, controller = make_navigation(GridMap(4, 1), Vec3(0, 0), Vec3(0, 0))
    assert controller.state == NavigationState.ARRIVED
    controller.set_goal(Vec3(3, 0))
    run_until_arrival(controller)
    assert motor.position.distance_to(Vec3(3, 0)) < 1e-6


def test_controller_accepts_3d_backend_without_grid() -> None:
    class FreeSpace:
        revision = 0

        def plan(self, start: Vec3, goal: Vec3) -> Route:
            return Route((goal,))

        def route_is_valid(self, position: Vec3, waypoints: Sequence[Vec3]) -> bool:
            return True

        def can_traverse(self, start: Vec3, end: Vec3) -> bool:
            return True

    backend = FreeSpace()
    motor = SimulatedMotor(backend, Vec3(0, 0, 0))
    controller = NavigationController(backend, motor)
    controller.set_goal(Vec3(3, 4, 5))
    run_until_arrival(controller)
    assert motor.position.distance_to(Vec3(3, 4, 5)) < 1e-6
