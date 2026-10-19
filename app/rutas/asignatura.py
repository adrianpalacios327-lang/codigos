from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from base_datos import obtener_sesion
from app.modelos.asignatura import Asignatura

router = APIRouter(prefix="/asignatura", tags=["Asignaturas"])

@router.get("/", response_model=list[Asignatura])
def listar_asignaturas(sesion: Session = Depends(obtener_sesion)):
    statement = select(Asignatura)
    return sesion.exec(statement).all()

@router.post("/", response_model=Asignatura, status_code=status.HTTP_201_CREATED)
def crear_asignatura(asignatura: Asignatura, sesion: Session = Depends(obtener_sesion)):
    sesion.add(asignatura)
    sesion.commit()
    sesion.refresh(asignatura)
    return asignatura

@router.get("/{id_asignatura}", response_model=Asignatura)
def obtener_asignatura(id_asignatura: int, sesion: Session = Depends(obtener_sesion)):
    asignatura = sesion.get(Asignatura, id_asignatura)
    if not asignatura:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada.")
    return asignatura

@router.put("/{id_asignatura}", response_model=Asignatura)
def actualizar_asignatura(id_asignatura: int, datos_asignatura: Asignatura, sesion: Session = Depends(obtener_sesion)):
    asignatura_db = sesion.get(Asignatura, id_asignatura)
    if not asignatura_db:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada.")
    
    datos_dict = datos_asignatura.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        if key != "id_asignatura":
            setattr(asignatura_db, key, value)
            
    sesion.add(asignatura_db)
    sesion.commit()
    sesion.refresh(asignatura_db)
    return asignatura_db

@router.delete("/{id_asignatura}", status_code=status.HTTP_200_OK)
def eliminar_asignatura(id_asignatura: int, sesion: Session = Depends(obtener_sesion)):
    asignatura_db = sesion.get(Asignatura, id_asignatura)
    if not asignatura_db:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada.")
    
    sesion.delete(asignatura_db)
    sesion.commit()
    return {"mensaje": f"Asignatura con ID {id_asignatura} eliminada correctamente."}