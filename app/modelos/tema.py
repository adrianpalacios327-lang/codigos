from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modelos.modulo import Modulo

class Tema(SQLModel, table=True):
    __tablename__ = "tema"

    id_tema: Optional[int] = Field(default=None, primary_key=True)
    id_modulo: int = Field(foreign_key="modulo.id_modulo")
    nombre: str = Field(max_length=150)
    descripcion: Optional[str] = None
    numero_tema: int
    duracion_estimada: Optional[int] = None

    modulo: Optional["Modulo"] = Relationship(back_populates="temas")