from pydantic import BaseModel


class UsuarioCrear(BaseModel):
    nombre: str
    correo: str
    contraseña: str


class UsuarioLogin(BaseModel):
    correo: str
    contraseña: str


class UsuarioRespuesta(BaseModel):
    id_usuario: int
    nombre: str
    correo: str
    rol: str

    class Config:
        from_attributes = True