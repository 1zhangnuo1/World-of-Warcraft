import json
import subprocess
import sys
from pathlib import Path

import pytest

from navigation_lab.core.controller import NavigationState
from navigation_lab.simulation.scenario import Simulation, SimulationConfig


@pytest.mark.parametrize("seed", range(12))
def test_full_dynamic_loop_reaches_real_goal_without_crossing_obstacles(seed: int) -> None:
    sim = Simulation(SimulationConfig(seed=seed))
    for _ in range(60 * 60):
        before = sim.motor.position
        sim.tick()
        assert sim.backend.can_traverse(before, sim.motor.position)
        assert before.distance_to(sim.motor.position) <= sim.config.speed / 60 + 1e-7
        if sim.arrived:
            break
    assert sim.arrived
    assert sim.motor.position.distance_to(sim.backend.center(sim.goal)) < 1e-6
    assert sim.controller.invalidations >= 1
    assert sim.controller.stuck_count >= 1
    assert sim.controller.replan_count >= 2
    assert sim.motor.distance_travelled >= 24
    assert any(event.kind == "arrived" for event in sim.controller.events)


def test_pause_does_not_advance_motion_faults_expiry_or_stuck_clock() -> None:
    sim = Simulation()
    sim.spawn_obstacle()
    sim.inject_jam()
    sim.paused = True
    before = sim.report()
    obstacles = sim.grid.obstacles
    for _ in range(1000):
        sim.tick()
    assert sim.report() == before
    assert sim.grid.obstacles == obstacles
    sim.paused = False
    sim.tick()
    assert sim.time > 0


def test_obstacles_expire_and_protected_cells_cannot_be_edited() -> None:
    sim = Simulation(SimulationConfig(auto_obstacles=False, demo_jam=False))
    for cell in sim.protected_cells:
        sim.toggle_obstacle(cell)
        assert sim.grid.contains(cell)
    sim.spawn_obstacle()
    created = sim.grid.obstacles
    for _ in range(300):
        sim.tick()
    assert not created & sim.grid.obstacles


def test_reproducible_seed() -> None:
    first, second = Simulation(), Simulation()
    for _ in range(1000):
        first.tick()
        second.tick()
    assert first.report() == second.report()


def test_boundary_edit_cannot_create_obstacle_touching_agent() -> None:
    sim = Simulation(SimulationConfig(auto_obstacles=False, demo_jam=False))
    for _ in range(36):
        sim.tick()
    assert sim.motor.position.x == pytest.approx(2.5)
    assert {(2, 1), (3, 1)} <= sim.protected_cells
    for cell in ((2, 1), (3, 1)):
        sim.toggle_obstacle(cell)
        assert cell not in sim.grid.obstacles
    assert sim.backend.can_traverse(sim.motor.position, sim.motor.position)


def test_manual_blockage_waits_and_recovers_after_removal() -> None:
    sim = Simulation(SimulationConfig(auto_obstacles=False, demo_jam=False))
    for cell in ((12, 13), (13, 12), (14, 13), (13, 14)):
        sim.toggle_obstacle(cell)
    for _ in range(120):
        sim.tick()
    assert sim.controller.state == NavigationState.WAITING
    assert sim.controller.stuck_count == 0
    sim.toggle_obstacle((13, 12))
    for _ in range(1200):
        sim.tick()
        if sim.arrived:
            break
    assert sim.arrived


def test_cli_headless_requires_no_pygame_and_writes_report(tmp_path: Path) -> None:
    report = tmp_path / "中文报告.json"
    code = (
        "import sys; from navigation_lab.app import main; "
        "result = main(['--headless', '--report', sys.argv[1]]); "
        "assert 'pygame' not in sys.modules; raise SystemExit(result)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code, str(report)], capture_output=True, text=True, check=True
    )
    assert json.loads(completed.stdout)["arrived"]
    assert json.loads(report.read_text(encoding="utf-8"))["arrived"]


def test_cli_timeout_returns_failure() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "navigation_lab", "--headless", "--max-seconds", "0.1"],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert not json.loads(completed.stdout)["arrived"]
