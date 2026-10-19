import secrets
from datetime import datetime, timezone
from typing import Optional

import bcrypt
from sqlmodel import Session, select

from app.modelos.usuario import Usuario
from app.esquemas.usuario import UsuarioCrear, UsuarioGoogle


PREFIJO_GOOGLE_ANTIGUO = "google_oauth_"


# ============================================================
# CONTRASEÑAS (hash con bcrypt)
# ============================================================

def hashear_contrasena(clave: str) -> str:
    return bcrypt.hashpw(clave.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verificar_contrasena(clave: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(clave.encode("utf-8")[:72], hash_guardado.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def es_hash_bcrypt(valor: str) -> bool:
    return valor.startswith(("$2a$", "$2b$", "$2y$"))


def _clave_aleatoria_hasheada() -> str:
    return hashear_contrasena(secrets.token_urlsafe(32))


def _normalizar_correo(correo: str) -> str:
    return correo.strip().lower()


# ============================================================
# CONSULTAS
# ============================================================

def obtener_usuario_por_correo(sesion: Session, correo: str) -> Optional[Usuario]:
    statement = select(Usuario).where(Usuario.correo == _normalizar_correo(correo))
    return sesion.exec(statement).first()


# ============================================================
# REGISTRO NORMAL
# ============================================================

def crear_usuario(sesion: Session, usuario: UsuarioCrear) -> Usuario:
    ahora = datetime.now(timezone.utc)
    db_usuario = Usuario(
        nombre=usuario.nombre.strip(),
        correo=_normalizar_correo(usuario.correo),
        contraseña=hashear_contrasena(usuario.contraseña),
        acepto_terminos=usuario.acepto_terminos,
        version_politica=(usuario.version_politica or "")[:20] or None,
        fecha_aceptacion=ahora if usuario.acepto_terminos else None,
    )
    sesion.add(db_usuario)
    sesion.commit()
    sesion.refresh(db_usuario)
    return db_usuario


# ============================================================
# LOGIN NORMAL
# ============================================================

def autenticar_usuario(sesion: Session, correo: str, clave: str) -> Optional[Usuario]:
    usuario = obtener_usuario_por_correo(sesion, correo)
    if not usuario:
        return None

    guardada = usuario.contraseña or ""

    if es_hash_bcrypt(guardada):
        return usuario if verificar_contrasena(clave, guardada) else None

    if guardada.startswith(PREFIJO_GOOGLE_ANTIGUO):
        return None

    if secrets.compare_digest(guardada.encode("utf-8"), clave.encode("utf-8")):
        usuario.contraseña = hashear_contrasena(clave)
        sesion.add(usuario)
        sesion.commit()
        sesion.refresh(usuario)
        return usuario

    return None


# ============================================================
# GOOGLE
# ============================================================

def crear_usuario_google(sesion: Session, datos: UsuarioGoogle) -> Usuario:
    ahora = datetime.now(timezone.utc)
    usuario = Usuario(
        nombre=datos.nombre.strip() or "Usuario Google",
        correo=_normalizar_correo(datos.correo),
        contraseña=_clave_aleatoria_hasheada(),
        acepto_terminos=datos.acepto_terminos,
        version_politica=(datos.version_politica or "")[:20] or None,
        fecha_aceptacion=ahora if datos.acepto_terminos else None,
    )
    sesion.add(usuario)
    sesion.commit()
    sesion.refresh(usuario)
    return usuario