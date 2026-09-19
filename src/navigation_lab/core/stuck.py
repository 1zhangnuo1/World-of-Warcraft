from dataclasses import dataclass

from navigation_lab.core.geometry import Vec3


@dataclass(slots=True)
class StuckDetector:
    """Measure net displacement from an anchor in simulation time, ignoring tiny jitter."""

    timeout: float = 1.25
    minimum_displacement: float = 0.06
    stalled_for: float = 0.0
    _anchor: Vec3 | None = None

    def reset(self, position: Vec3) -> None:
        self._anchor = position
        self.stalled_for = 0.0

    def observe(self, position: Vec3, dt: float, expected_to_move: bool) -> bool:
        if self._anchor is None or not expected_to_move:
            self.reset(position)
            return False
        if position.distance_to(self._anchor) >= self.minimum_displacement:
            self.reset(position)
            return False
        self.stalled_for += dt
        return self.stalled_for >= self.timeout
