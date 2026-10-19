from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modelos.plan_estudio import PlanDeEstudio
    from app.modelos.tema import Tema

class Modulo(SQLModel, table=True):
    __tablename__ = "modulo"

    id_modulo: Optional[int] = Field(default=None, primary_key=True)
    id_plan: int = Field(foreign_key="plan_de_estudio.id_plan")
    nombre: str = Field(max_length=150)
    descripcion: Optional[str] = None
    numero_modulo: int
    objetivo: Optional[str] = None
    estado: Optional[str] = Field(default="activo", max_length=50)

    plan: Optional["PlanDeEstudio"] = Relationship(back_populates="modulos")
    temas: List["Tema"] = Relationship(back_populates="modulo")