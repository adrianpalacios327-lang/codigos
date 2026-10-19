from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from base_datos import obtener_sesion
from app.modelos.modulo import Modulo

router = APIRouter(prefix="/modulo", tags=["Módulos"])

@router.get("/", response_model=list[Modulo])
def listar_todos_los_modulos(sesion: Session = Depends(obtener_sesion)):
    modulos = sesion.exec(select(Modulo)).all()
    return modulos

@router.get("/{id_modulo}", response_model=Modulo)
def obtener_modulo(id_modulo: int, sesion: Session = Depends(obtener_sesion)):
    modulo = sesion.get(Modulo, id_modulo)
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado.")
    return modulo

@router.get("/plan/{id_plan}", response_model=list[Modulo])
def listar_modulos_por_plan(id_plan: int, sesion: Session = Depends(obtener_sesion)):
    statement = select(Modulo).where(Modulo.id_plan == id_plan)
    return sesion.exec(statement).all()

@router.post("/", response_model=Modulo, status_code=status.HTTP_201_CREATED)
def crear_modulo(modulo: Modulo, sesion: Session = Depends(obtener_sesion)):
    sesion.add(modulo)
    sesion.commit()
    sesion.refresh(modulo)
    return modulo

@router.put("/{id_modulo}", response_model=Modulo)
def actualizar_modulo(id_modulo: int, datos_modulo: Modulo, sesion: Session = Depends(obtener_sesion)):
    modulo_db = sesion.get(Modulo, id_modulo)
    if not modulo_db:
        raise HTTPException(status_code=404, detail="Módulo no encontrado.")
    
    datos_dict = datos_modulo.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        if key != "id_modulo":
            setattr(modulo_db, key, value)
            
    sesion.add(modulo_db)
    sesion.commit()
    sesion.refresh(modulo_db)
    return modulo_db

@router.delete("/{id_modulo}", status_code=status.HTTP_200_OK)
def eliminar_modulo(id_modulo: int, sesion: Session = Depends(obtener_sesion)):
    modulo_db = sesion.get(Modulo, id_modulo)
    if not modulo_db:
        raise HTTPException(status_code=404, detail="Módulo no encontrado.")
    
    sesion.delete(modulo_db)
    sesion.commit()
    return {"mensaje": f"Módulo con ID {id_modulo} eliminado correctamente."}