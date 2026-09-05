from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modelos.chat_ia import ChatIA
    from app.modelos.plan_de_estudio import PlanDeEstudio
    from app.modelos.sesion_de_estudio import SesionDeEstudio


class RolUsuario(str, Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    ESTUDIANTE = "ESTUDIANTE"


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    correo: str = Field(max_length=150, unique=True, index=True)
    contraseña: str = Field(max_length=255)
    rol: RolUsuario = Field(default=RolUsuario.ESTUDIANTE)

    chats: List["ChatIA"] = Relationship(back_populates="usuario")
    planes: List["PlanDeEstudio"] = Relationship(back_populates="usuario")
    sesiones: List["SesionDeEstudio"] = Relationship(back_populates="usuario")
    