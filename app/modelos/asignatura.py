from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modelos.plan_estudio import PlanDeEstudio


class NivelDificultad(str, Enum):
    BASICO = "BASICO"
    INTERMEDIO = "INTERMEDIO"
    AVANZADO = "AVANZADO"


class Asignatura(SQLModel, table=True):
    __tablename__ = "asignatura"

    id_asignatura: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    descripcion: Optional[str] = None
    nivel_dificultad: Optional[str] = Field(default="BASICO", max_length=50)

    planes: List["PlanDeEstudio"] = Relationship(back_populates="asignatura")

