from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modelos.usuario import Usuario
    from app.modelos.plan_estudio import PlanDeEstudio

class ControlFatiga(SQLModel, table=True):
    __tablename__ = "control_fatiga"

    id_fatiga: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: int = Field(foreign_key="usuario.id_usuario")
    id_plan: int = Field(foreign_key="plan_de_estudio.id_plan")
    nivel_fatiga: Optional[int] = None
    fecha_registro: datetime = Field(default_factory=datetime.now)
    observacion: Optional[str] = None

    usuario: Optional["Usuario"] = Relationship(back_populates="fatigas")
    plan: Optional["PlanDeEstudio"] = Relationship(back_populates="fatigas")