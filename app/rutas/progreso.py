from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from base_datos import obtener_sesion
from app.modelos.progreso import Progreso

router = APIRouter(prefix="/progreso", tags=["Progreso del Estudiante"])

@router.get("/", response_model=list[Progreso])
def listar_todos_los_progresos(sesion: Session = Depends(obtener_sesion)):
    progresos = sesion.exec(select(Progreso)).all()
    return progresos

@router.get("/{id_progreso}", response_model=Progreso)
def obtener_progreso(id_progreso: int, sesion: Session = Depends(obtener_sesion)):
    progreso = sesion.get(Progreso, id_progreso)
    if not progreso:
        raise HTTPException(status_code=404, detail="Registro de progreso no encontrado.")
    return progreso

@router.get("/plan/{id_plan}/usuario/{id_usuario}")
def obtener_progreso_plan(id_plan: int, id_usuario: int, sesion: Session = Depends(obtener_sesion)):
    statement = select(Progreso).where(
        Progreso.id_plan == id_plan,
        Progreso.id_usuario == id_usuario
    )
    registros = sesion.exec(statement).all()
    
    temas_completados = sum(1 for r in registros if getattr(r, "completado", False))
    temas_totales = len(registros)
    porcentaje = (temas_completados / temas_totales * 100) if temas_totales > 0 else 0.0

    return {
        "id_plan": id_plan,
        "id_usuario": id_usuario,
        "porcentaje_avance": round(porcentaje, 2),
        "temas_completados": temas_completados,
        "temas_totales": temas_totales,
        "registros": registros
    }

@router.post("/", response_model=Progreso, status_code=status.HTTP_201_CREATED)
def crear_o_actualizar_progreso(progreso: Progreso, sesion: Session = Depends(obtener_sesion)):
    existente = sesion.exec(
        select(Progreso).where(
            Progreso.id_usuario == progreso.id_usuario,
            Progreso.id_plan == progreso.id_plan,
            Progreso.id_modulo == progreso.id_modulo,
            Progreso.id_tema == progreso.id_tema
        )
    ).first()
    if existente:
        existente.completado = progreso.completado
        existente.porcentaje = progreso.porcentaje
        sesion.add(existente)
        sesion.commit()
        sesion.refresh(existente)
        return existente

    sesion.add(progreso)
    sesion.commit()
    sesion.refresh(progreso)
    return progreso

@router.put("/{id_progreso}", response_model=Progreso)
def actualizar_progreso(id_progreso: int, datos_progreso: Progreso, sesion: Session = Depends(obtener_sesion)):
    progreso_db = sesion.get(Progreso, id_progreso)
    if not progreso_db:
        raise HTTPException(status_code=404, detail="Registro de progreso no encontrado.")
    
    datos_dict = datos_progreso.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        if key != "id_progreso":
            setattr(progreso_db, key, value)
            
    sesion.add(progreso_db)
    sesion.commit()
    sesion.refresh(progreso_db)
    return progreso_db

@router.delete("/{id_progreso}", status_code=status.HTTP_200_OK)
def eliminar_progreso(id_progreso: int, sesion: Session = Depends(obtener_sesion)):
    progreso_db = sesion.get(Progreso, id_progreso)
    if not progreso_db:
        raise HTTPException(status_code=404, detail="Registro de progreso no encontrado.")
    
    sesion.delete(progreso_db)
    sesion.commit()
    return {"mensaje": f"Registro de progreso con ID {id_progreso} eliminado correctamente."}