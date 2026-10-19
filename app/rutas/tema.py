from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from base_datos import obtener_sesion
from app.modelos.tema import Tema

router = APIRouter(prefix="/tema", tags=["Temas"])

@router.get("/modulo/{id_modulo}", response_model=list[Tema])
def listar_temas_por_modulo(id_modulo: int, sesion: Session = Depends(obtener_sesion)):
    statement = select(Tema).where(Tema.id_modulo == id_modulo)
    return sesion.exec(statement).all()

@router.get("/{id_tema}", response_model=Tema)
def obtener_detalle_tema(id_tema: int, sesion: Session = Depends(obtener_sesion)):
    tema = sesion.get(Tema, id_tema)
    if not tema:
        raise HTTPException(status_code=404, detail="Tema no encontrado.")
    return tema