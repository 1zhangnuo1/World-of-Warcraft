from navigation_lab.core.contracts import NavigationBackend
from navigation_lab.core.geometry import Vec3


class SimulatedMotor:
    """Continuous world-space motion with collision checks and independent fault injection."""

    def __init__(self, backend: NavigationBackend, position: Vec3, speed: float = 2.5) -> None:
        if speed <= 0:
            raise ValueError("speed must be positive")
        self.backend = backend
        self._position = position
        self.speed = speed
        self.blocked = False
        self.distance_travelled = 0.0

    @property
    def position(self) -> Vec3:
        return self._position

    def move_towards(self, target: Vec3, dt: float) -> None:
        if self.blocked or dt <= 0:
            return
        candidate = self.position.towards(target, self.speed * dt)
        if self.backend.can_traverse(self.position, candidate):
            self.distance_travelled += self.position.distance_to(candidate)
            self._position = candidate
