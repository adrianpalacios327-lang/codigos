from typing import Optional, List, Any, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from app.modelos.usuario import Usuario
    from app.modelos.asignatura import Asignatura
    from app.modelos.modulo import Modulo
    from app.modelos.progreso import Progreso
    from app.modelos.control_fatiga import ControlFatiga
    from app.modelos.sesion_estudio import SesionEstudio
    from app.modelos.prompt_ia import PromptIA


class PlanDeEstudio(SQLModel, table=True):
    __tablename__ = "plan_de_estudio"

    id_plan: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: int = Field(foreign_key="usuario.id_usuario")
    id_asignatura: int = Field(foreign_key="asignatura.id_asignatura")
    titulo: str = Field(max_length=150)
    descripcion: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_actualizacion: datetime = Field(default_factory=datetime.now)
    estado: Optional[str] = Field(default="activo", max_length=50)
    nivel_objetivo: Optional[str] = Field(default=None, max_length=50)
    duracion: Optional[int] = None
    id_ruta: Optional[int] = Field(default=None)
    contenido_json: Optional[Any] = Field(default=None, sa_column=Column(JSONB))

    usuario: Optional["Usuario"] = Relationship(back_populates="planes")
    asignatura: Optional["Asignatura"] = Relationship(back_populates="planes")
    modulos: List["Modulo"] = Relationship(back_populates="plan")
    progresos: List["Progreso"] = Relationship(back_populates="plan")
    fatigas: List["ControlFatiga"] = Relationship(back_populates="plan")
    sesiones: List["SesionEstudio"] = Relationship(back_populates="plan")
    prompts: List["PromptIA"] = Relationship(back_populates="plan")