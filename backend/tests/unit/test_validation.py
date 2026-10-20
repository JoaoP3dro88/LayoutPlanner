from app.domain.models import Footprint, Instance, IssueCode, Layout, ObjectType, Room
from app.domain.validation import validate_layout

RECT_ROOM = Room(outline=[(0, 0), (10000, 0), (10000, 6000), (0, 6000)])
MAQ = ObjectType(id="maq", name="Máquina", footprint=Footprint.rect(1200, 800))


def layout(instances, room=RECT_ROOM, types=(MAQ,)):
    return Layout(room=room, types=list(types), instances=instances)


def codes(rep):
    return {i.code for i in rep.issues}


def test_valid_layout_and_bom():
    rep = validate_layout(
        layout(
            [Instance(id="a", type_id="maq", x=1000, y=1000), Instance(id="b", type_id="maq", x=3000, y=1000)]
        )
    )
    assert rep.ok and rep.bom == {"maq": 2}
    assert 0 < rep.utilization < 1


def test_touching_is_not_collision():
    rep = validate_layout(
        layout(
            [Instance(id="a", type_id="maq", x=1000, y=1000), Instance(id="b", type_id="maq", x=2200, y=1000)]
        )
    )
    assert rep.ok


def test_collision():
    rep = validate_layout(
        layout(
            [Instance(id="a", type_id="maq", x=1000, y=1000), Instance(id="b", type_id="maq", x=1500, y=1000)]
        )
    )
    assert codes(rep) == {IssueCode.COLLISION}


def test_rotation_changes_footprint():
    ok = validate_layout(
        layout(
            [
                Instance(id="a", type_id="maq", x=1000, y=1000, rotation=90),
                Instance(id="b", type_id="maq", x=1800, y=1000, rotation=90),
            ]
        )
    )
    assert ok.ok
    bad = validate_layout(
        layout(
            [Instance(id="a", type_id="maq", x=1000, y=1000), Instance(id="b", type_id="maq", x=1800, y=1000)]
        )
    )
    assert IssueCode.COLLISION in codes(bad)


def test_outside_room():
    rep = validate_layout(layout([Instance(id="a", type_id="maq", x=100, y=1000)]))
    assert codes(rep) == {IssueCode.OUTSIDE_ROOM}


def test_l_shaped_room_notch_is_outside():
    l_room = Room(outline=[(0, 0), (10000, 0), (10000, 3000), (4000, 3000), (4000, 6000), (0, 6000)])
    rep = validate_layout(layout([Instance(id="a", type_id="maq", x=7000, y=4500)], room=l_room))
    assert codes(rep) == {IssueCode.OUTSIDE_ROOM}


def test_obstacle_pillar():
    room = Room(outline=RECT_ROOM.outline, obstacles=[[(900, 900), (1100, 900), (1100, 1100), (900, 1100)]])
    rep = validate_layout(layout([Instance(id="a", type_id="maq", x=1000, y=1000)], room=room))
    assert IssueCode.ON_OBSTACLE in codes(rep)


def test_rotation_not_allowed():
    t = MAQ.model_copy(update={"rotations": [0, 180]})
    rep = validate_layout(layout([Instance(id="a", type_id="maq", x=1000, y=1000, rotation=90)], types=(t,)))
    assert IssueCode.ROTATION_NOT_ALLOWED in codes(rep)


def test_performance_137_objects():
    insts = [
        Instance(id=f"i{n}", type_id="maq", x=700 + (n % 12) * 1300, y=600 + (n // 12) * 900)
        for n in range(137)
    ]
    big = Room(outline=[(0, 0), (20000, 0), (20000, 12000), (0, 12000)])
    assert validate_layout(layout(insts, room=big)).ok
