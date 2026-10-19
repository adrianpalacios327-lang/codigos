from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from base_datos import obtener_sesion  # Ajusta si tu función de sesión está en otro archivo
from app.crud.usuario import (
    crear_usuario,
    autenticar_usuario,
    obtener_usuario_por_correo,
    crear_usuario_google
)
from app.esquemas.usuario import (
    UsuarioCrear,
    UsuarioLogin,
    UsuarioRespuesta,
    UsuarioGoogle
)

# Prefijo en singular para coincidir con POST /usuario/registro
router = APIRouter(prefix="/usuario", tags=["Usuarios"])


@router.post("/registro", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
def registrar_usuario(datos: UsuarioCrear, sesion: Session = Depends(obtener_sesion)):
    existente = obtener_usuario_por_correo(sesion, datos.correo)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya se encuentra registrado."
        )
    return crear_usuario(sesion, datos)


@router.post("/login")
def login(datos: UsuarioLogin, sesion: Session = Depends(obtener_sesion)):
    usuario = autenticar_usuario(sesion, datos.correo, datos.contraseña)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos."
        )
    return {
        "mensaje": "Inicio de sesión exitoso",
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "rol": usuario.rol
    }


@router.post("/google", response_model=UsuarioRespuesta)
def login_o_registro_google(datos: UsuarioGoogle, sesion: Session = Depends(obtener_sesion)):
    usuario = obtener_usuario_por_correo(sesion, datos.correo)
    if not usuario:
        usuario = crear_usuario_google(sesion, datos)
    return usuario