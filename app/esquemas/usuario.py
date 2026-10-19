from typing import Optional
from pydantic import BaseModel, ConfigDict


class UsuarioCrear(BaseModel):
    nombre: str
    correo: str
    contraseña: str
    acepto_terminos: bool = False
    version_politica: Optional[str] = None


class UsuarioLogin(BaseModel):
    correo: str
    contraseña: str


class UsuarioGoogle(BaseModel):
    nombre: str
    correo: str
    google_id: Optional[str] = None
    foto: Optional[str] = None
    acepto_terminos: bool = False
    version_politica: Optional[str] = None


class UsuarioRespuesta(BaseModel):
    id_usuario: int
    nombre: str
    correo: str
    rol: Optional[str] = "ESTUDIANTE"

    model_config = ConfigDict(from_attributes=True)