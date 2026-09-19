from dataclasses import dataclass
from math import dist


@dataclass(frozen=True, slots=True)
class Vec3:
    """World coordinates. Grid uses z=0; the core does not assume a 2D plane."""

    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: "Vec3") -> float:
        return dist((self.x, self.y, self.z), (other.x, other.y, other.z))

    def towards(self, target: "Vec3", distance: float) -> "Vec3":
        length = self.distance_to(target)
        if length <= distance or length == 0:
            return target
        ratio = max(0.0, distance) / length
        return Vec3(
            self.x + (target.x - self.x) * ratio,
            self.y + (target.y - self.y) * ratio,
            self.z + (target.z - self.z) * ratio,
        )
