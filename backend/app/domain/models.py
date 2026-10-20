"""Modelo de dados do planejador de layout.

Convenções:
- Unidade: milímetros.
- Eixos matemáticos (X para a direita, Y para cima). O frontend, que usa Y para baixo,
  converte na borda da API.
- Rotação em graus, sentido anti-horário, em torno da origem LOCAL do tipo.
- Footprint em coordenadas locais (origem = ponto de referência do objeto).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator
from shapely.geometry import Polygon

Point = tuple[float, float]


class Dir(StrEnum):
    N = "N"
    E = "E"
    S = "S"
    W = "W"


class PortKind(StrEnum):
    INPUT = "input"
    OUTPUT = "output"


class Port(BaseModel):
    id: str
    kind: PortKind
    pos: Point  # coordenadas locais
    dir: Dir  # lado por onde o material entra/sai (local, sem rotação)


class Footprint(BaseModel):
    points: list[Point] = Field(min_length=3)

    @model_validator(mode="after")
    def _valid_polygon(self) -> Footprint:
        poly = Polygon(self.points)
        if not poly.is_valid or poly.area <= 0:
            raise ValueError("footprint inválido (auto-interseção ou área zero)")
        return self

    @classmethod
    def rect(cls, a: float, b: float) -> Footprint:
        """Retângulo A x B centrado na origem."""
        x, y = a / 2, b / 2
        return cls(points=[(-x, -y), (x, -y), (x, y), (-x, y)])


class ObjectType(BaseModel):
    id: str
    name: str
    footprint: Footprint
    ports: list[Port] = []
    rotations: list[float] = [0, 90, 180, 270]
    color: str = "#888888"


class Instance(BaseModel):
    id: str
    type_id: str
    x: float
    y: float
    rotation: float = 0
    fixed: bool = False  # o otimizador (etapa futura) não move instâncias fixas


class Room(BaseModel):
    outline: list[Point] = Field(min_length=3)
    obstacles: list[list[Point]] = []  # pilares, áreas proibidas

    @model_validator(mode="after")
    def _valid_polygons(self) -> Room:
        for pts in [self.outline, *self.obstacles]:
            if len(pts) < 3 or not Polygon(pts).is_valid:
                raise ValueError("polígono da sala/obstáculo inválido")
        return self


class Layout(BaseModel):
    room: Room
    types: list[ObjectType]
    instances: list[Instance]

    @model_validator(mode="after")
    def _references(self) -> Layout:
        type_ids = [t.id for t in self.types]
        if len(set(type_ids)) != len(type_ids):
            raise ValueError("ids de tipo duplicados")
        inst_ids = [i.id for i in self.instances]
        if len(set(inst_ids)) != len(inst_ids):
            raise ValueError("ids de instância duplicados")
        unknown = {i.type_id for i in self.instances} - set(type_ids)
        if unknown:
            raise ValueError(f"tipos inexistentes: {sorted(unknown)}")
        return self


class IssueCode(StrEnum):
    COLLISION = "collision"
    OUTSIDE_ROOM = "outside_room"
    ON_OBSTACLE = "on_obstacle"
    ROTATION_NOT_ALLOWED = "rotation_not_allowed"


class Issue(BaseModel):
    code: IssueCode
    message: str
    instance_ids: list[str]


class Report(BaseModel):
    ok: bool
    issues: list[Issue]
    bom: dict[str, int]  # type_id -> quantidade
    room_area: float  # mm²
    occupied_area: float  # mm²
    utilization: float  # 0..1
