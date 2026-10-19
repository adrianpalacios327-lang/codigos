from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from base_datos import obtener_sesion
from pydantic import BaseModel
from app.modelos.control_fatiga import ControlFatiga

router = APIRouter(prefix="/control-fatiga", tags=["Control de Fatiga"])

class RegistroFatigaSchema(BaseModel):
    id_usuario: int
    minutos_estudiados: int
    nivel_cansancio: int  # Escala de 1 a 5

@router.get("/", response_model=list[ControlFatiga])
def listar_registros_fatiga(sesion: Session = Depends(obtener_sesion)):
    registros = sesion.exec(select(ControlFatiga)).all()
    return registros

@router.get("/{id_fatiga}", response_model=ControlFatiga)
def obtener_registro_fatiga(id_fatiga: int, sesion: Session = Depends(obtener_sesion)):
    registro = sesion.get(ControlFatiga, id_fatiga)
    if not registro:
        raise HTTPException(status_code=404, detail="Registro de fatiga no encontrado.")
    return registro

@router.get("/usuario/{id_usuario}", response_model=list[ControlFatiga])
def obtener_estado_fatiga_usuario(id_usuario: int, sesion: Session = Depends(obtener_sesion)):
    statement = select(ControlFatiga).where(ControlFatiga.id_usuario == id_usuario)
    return sesion.exec(statement).all()

@router.post("/", response_model=ControlFatiga, status_code=status.HTTP_201_CREATED)
def registrar_nivel_fatiga(datos: ControlFatiga, sesion: Session = Depends(obtener_sesion)):
    sesion.add(datos)
    sesion.commit()
    sesion.refresh(datos)
    return datos

@router.put("/{id_fatiga}", response_model=ControlFatiga)
def actualizar_registro_fatiga(id_fatiga: int, datos_fatiga: ControlFatiga, sesion: Session = Depends(obtener_sesion)):
    fatiga_db = sesion.get(ControlFatiga, id_fatiga)
    if not fatiga_db:
        raise HTTPException(status_code=404, detail="Registro de fatiga no encontrado.")
    
    datos_dict = datos_fatiga.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        if key != "id_fatiga":
            setattr(fatiga_db, key, value)
            
    sesion.add(fatiga_db)
    sesion.commit()
    sesion.refresh(fatiga_db)
    return fatiga_db

@router.delete("/{id_fatiga}", status_code=status.HTTP_200_OK)
def eliminar_registro_fatiga(id_fatiga: int, sesion: Session = Depends(obtener_sesion)):
    fatiga_db = sesion.get(ControlFatiga, id_fatiga)
    if not fatiga_db:
        raise HTTPException(status_code=404, detail="Registro de fatiga no encontrado.")
    
    sesion.delete(fatiga_db)
    sesion.commit()
    return {"mensaje": f"Registro de fatiga con ID {id_fatiga} eliminado correctamente."}