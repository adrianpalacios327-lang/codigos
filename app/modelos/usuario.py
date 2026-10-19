from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column
import sqlalchemy as sa

if TYPE_CHECKING:
    from app.modelos.plan_estudio import PlanDeEstudio
    from app.modelos.progreso import Progreso
    from app.modelos.control_fatiga import ControlFatiga
    from app.modelos.sesion_estudio import SesionEstudio


class RolUsuario(str, Enum):
    ESTUDIANTE = "ESTUDIANTE"
    DOCENTE = "DOCENTE"
    ADMINISTRADOR = "ADMINISTRADOR"


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"
    __table_args__ = {"extend_existing": True}

    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    correo: str = Field(max_length=150, unique=True, index=True)
    
    contraseña: str = Field(sa_column=Column("contrase\u00f1a", sa.String(255), nullable=False))

    rol: RolUsuario = Field(
        default=RolUsuario.ESTUDIANTE,
        sa_column=Column(sa.Enum(RolUsuario, name="rolusuario"), nullable=False, server_default="ESTUDIANTE")
    )

    acepto_terminos: bool = Field(default=False)
    version_politica: Optional[str] = Field(default=None, max_length=20)
    fecha_aceptacion: Optional[datetime] = Field(default=None)

    planes: List["PlanDeEstudio"] = Relationship(back_populates="usuario")
    progresos: List["Progreso"] = Relationship(back_populates="usuario")
    fatigas: List["ControlFatiga"] = Relationship(back_populates="usuario")
    sesiones: List["SesionEstudio"] = Relationship(back_populates="usuario")