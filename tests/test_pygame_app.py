from pathlib import Path

import pytest

from navigation_lab.simulation.scenario import Simulation, SimulationConfig


def test_window_controls_render_and_exit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    import pygame

    from navigation_lab.presentation.pygame_app import PygameApp

    app = PygameApp(Simulation(SimulationConfig(auto_obstacles=False, demo_jam=False)))
    try:
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        assert app.simulation.paused
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        assert not app.simulation.paused
        cell = (2, 2)
        point = app.screen_point(app.simulation.backend.center(cell))
        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=point, button=1))
        assert cell in app.simulation.grid.obstacles
        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=point, button=1))
        assert cell not in app.simulation.grid.obstacles
        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=point, button=3))
        assert app.simulation.goal == cell
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j))
        assert app.simulation.motor.blocked
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        assert app.simulation.goal == (13, 13) and not app.simulation.motor.blocked
        screenshot = tmp_path / "screen.png"
        app.run(frames=2, screenshot=screenshot)
        assert screenshot.stat().st_size > 1000
    finally:
        pygame.quit()
