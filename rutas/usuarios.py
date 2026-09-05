from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from base_datos import obtener_sesion
from app.esquemas.usuario import UsuarioCrear, UsuarioLogin, UsuarioRespuesta
from app.crud.usuario import obtener_usuario_por_correo, crear_usuario
from app.modelos.usuario import Usuario

router = APIRouter(prefix="/usuario", tags=["Usuarios"])

@router.post("/registro", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
def registrar(usuario: UsuarioCrear, sesion: Session = Depends(obtener_sesion)):
    db_user = obtener_usuario_por_correo(sesion, usuario.correo)
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")
    return crear_usuario(sesion, usuario)

@router.post("/login", response_model=UsuarioRespuesta)
def login(credenciales: UsuarioLogin, sesion: Session = Depends(obtener_sesion)):
    usuario = obtener_usuario_por_correo(sesion, credenciales.correo)
    if not usuario or usuario.contraseña != credenciales.contraseña:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas.")
    return usuario

@router.get("/", response_model=list[UsuarioRespuesta])
def listar_usuarios(sesion: Session = Depends(obtener_sesion)):
    usuarios = sesion.exec(select(Usuario)).all()
    return usuarios

@router.get("/{id_usuario}", response_model=UsuarioRespuesta)
def obtener_usuario(id_usuario: int, sesion: Session = Depends(obtener_sesion)):
    usuario = sesion.get(Usuario, id_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return usuario

@router.put("/{id_usuario}", response_model=UsuarioRespuesta)
def actualizar_usuario(id_usuario: int, datos_actualizar: UsuarioCrear, sesion: Session = Depends(obtener_sesion)):
    usuario_db = sesion.get(Usuario, id_usuario)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    # Actualizar campos
    datos_dict = datos_actualizar.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        setattr(usuario_db, key, value)
        
    sesion.add(usuario_db)
    sesion.commit()
    sesion.refresh(usuario_db)
    return usuario_db

@router.delete("/{id_usuario}", status_code=status.HTTP_200_OK)
def eliminar_usuario(id_usuario: int, sesion: Session = Depends(obtener_sesion)):
    usuario_db = sesion.get(Usuario, id_usuario)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    sesion.delete(usuario_db)
    sesion.commit()
    return {"mensaje": f"Usuario con ID {id_usuario} eliminado correctamente."}