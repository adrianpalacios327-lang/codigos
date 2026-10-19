from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modelos.usuario import Usuario
    from app.modelos.plan_estudio import PlanDeEstudio

class Progreso(SQLModel, table=True):
    __tablename__ = "progreso"

    id_progreso: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: int = Field(foreign_key="usuario.id_usuario")
    id_plan: int = Field(foreign_key="plan_de_estudio.id_plan")
    id_modulo: int = Field(foreign_key="modulo.id_modulo")
    id_tema: int = Field(foreign_key="tema.id_tema")
    porcentaje: float = Field(default=0.0)
    completado: bool = Field(default=False)
    fecha_inicio: datetime = Field(default_factory=datetime.now)
    fecha_ultima_actividad: datetime = Field(default_factory=datetime.now)

    usuario: Optional["Usuario"] = Relationship(back_populates="progresos")
    plan: Optional["PlanDeEstudio"] = Relationship(back_populates="progresos")