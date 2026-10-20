from shapely import affinity
from shapely.geometry import Polygon

from .models import Instance, ObjectType


def place(obj_type: ObjectType, inst: Instance) -> Polygon:
    """Footprint do tipo, rotacionado e transladado para a posição da instância."""
    poly = Polygon(obj_type.footprint.points)
    poly = affinity.rotate(poly, inst.rotation, origin=(0, 0))
    return affinity.translate(poly, inst.x, inst.y)


def angle_allowed(angle: float, allowed: list[float]) -> bool:
    return any(abs((angle - r + 180) % 360 - 180) < 1e-6 for r in allowed)
