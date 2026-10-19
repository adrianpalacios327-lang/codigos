from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from base_datos import obtener_sesion
from app.modelos.sesion_estudio import SesionEstudio

router = APIRouter(prefix="/sesion-estudio", tags=["Sesiones de Estudio"])

@router.get("/", response_model=list[SesionEstudio])
def listar_todas_las_sesiones(sesion: Session = Depends(obtener_sesion)):
    sesiones = sesion.exec(select(SesionEstudio)).all()
    return sesiones

@router.get("/{id_sesion}", response_model=SesionEstudio)
def obtener_sesion_por_id(id_sesion: int, sesion: Session = Depends(obtener_sesion)):
    sesion_db = sesion.get(SesionEstudio, id_sesion)
    if not sesion_db:
        raise HTTPException(status_code=404, detail="Sesión de estudio no encontrada.")
    return sesion_db

@router.get("/usuario/{id_usuario}", response_model=list[SesionEstudio])
def listar_sesiones_usuario(id_usuario: int, sesion: Session = Depends(obtener_sesion)):
    statement = select(SesionEstudio).where(SesionEstudio.id_usuario == id_usuario)
    return sesion.exec(statement).all()

@router.post("/", response_model=SesionEstudio, status_code=status.HTTP_201_CREATED)
def registrar_sesion(datos: SesionEstudio, sesion: Session = Depends(obtener_sesion)):
    sesion.add(datos)
    sesion.commit()
    sesion.refresh(datos)
    return datos

@router.put("/{id_sesion}", response_model=SesionEstudio)
def actualizar_sesion(id_sesion: int, datos_sesion: SesionEstudio, sesion: Session = Depends(obtener_sesion)):
    sesion_db = sesion.get(SesionEstudio, id_sesion)
    if not sesion_db:
        raise HTTPException(status_code=404, detail="Sesión de estudio no encontrada.")
    
    datos_dict = datos_sesion.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        if key != "id_sesion":
            setattr(sesion_db, key, value)
            
    sesion.add(sesion_db)
    sesion.commit()
    sesion.refresh(sesion_db)
    return sesion_db

@router.delete("/{id_sesion}", status_code=status.HTTP_200_OK)
def eliminar_sesion(id_sesion: int, sesion: Session = Depends(obtener_sesion)):
    sesion_db = sesion.get(SesionEstudio, id_sesion)
    if not sesion_db:
        raise HTTPException(status_code=404, detail="Sesión de estudio no encontrada.")
    
    sesion.delete(sesion_db)
    sesion.commit()
    return {"mensaje": f"Sesión de estudio con ID {id_sesion} eliminada correctamente."}