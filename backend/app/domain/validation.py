from collections import Counter

from shapely.geometry import Polygon
from shapely.strtree import STRtree

from .geometry import angle_allowed, place
from .models import Issue, IssueCode, Layout, Report

TOL = 1.0  # mm² de sobreposição tolerada (encostar é permitido)


def validate_layout(layout: Layout) -> Report:
    types = {t.id: t for t in layout.types}
    room = Polygon(layout.room.outline)
    obstacles = [Polygon(o) for o in layout.room.obstacles]
    issues: list[Issue] = []

    ids = [i.id for i in layout.instances]
    geoms = [place(types[i.type_id], i) for i in layout.instances]

    for inst, g in zip(layout.instances, geoms, strict=False):
        t = types[inst.type_id]
        if not angle_allowed(inst.rotation, t.rotations):
            issues.append(
                Issue(
                    code=IssueCode.ROTATION_NOT_ALLOWED,
                    message=f"{inst.id}: rotação {inst.rotation}° não permitida para {t.name}",
                    instance_ids=[inst.id],
                )
            )
        if g.difference(room).area > TOL:
            issues.append(
                Issue(
                    code=IssueCode.OUTSIDE_ROOM,
                    message=f"{inst.id} ({t.name}) ultrapassa os limites da sala",
                    instance_ids=[inst.id],
                )
            )
        if any(g.intersection(o).area > TOL for o in obstacles):
            issues.append(
                Issue(
                    code=IssueCode.ON_OBSTACLE,
                    message=f"{inst.id} ({t.name}) está sobre um obstáculo/área proibida",
                    instance_ids=[inst.id],
                )
            )

    if geoms:
        tree = STRtree(geoms)
        for a, g in enumerate(geoms):
            for b in tree.query(g, predicate="intersects"):
                b = int(b)
                if b > a and g.intersection(geoms[b]).area > TOL:
                    issues.append(
                        Issue(
                            code=IssueCode.COLLISION,
                            message=f"{ids[a]} colide com {ids[b]}",
                            instance_ids=[ids[a], ids[b]],
                        )
                    )

    occupied = sum(g.area for g in geoms)
    return Report(
        ok=not issues,
        issues=issues,
        bom=dict(Counter(i.type_id for i in layout.instances)),
        room_area=room.area,
        occupied_area=occupied,
        utilization=occupied / room.area if room.area else 0.0,
    )
