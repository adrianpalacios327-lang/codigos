import os
import json
from typing import List, Optional
from dotenv import load_dotenv
from google import genai
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel

from base_datos import obtener_sesion
from app.modelos.plan_estudio import PlanDeEstudio
from app.modelos.modulo import Modulo
from app.modelos.tema import Tema
from app.modelos.asignatura import Asignatura
from app.modelos.usuario import Usuario

# Cargar variables de entorno
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

router = APIRouter(prefix="/plan-estudio", tags=["Planes de Estudio"])


# Esquemas de entrada
class GenerarPlanSchema(BaseModel):
    id_usuario: int
    titulo: str
    descripcion: Optional[str] = None
    nivel_objetivo: Optional[str] = "Intermedio"
    duracion: Optional[int] = 7
    id_asignatura: Optional[int] = None  # <--- Agregado
    id_ruta: Optional[int] = None        # <--- Agregado


class PlanAjustarSchema(BaseModel):
    indicaciones: str


@router.post("/generar", status_code=status.HTTP_201_CREATED)
def generar_y_crear_plan(solicitud: GenerarPlanSchema, sesion: Session = Depends(obtener_sesion)):
    """Genera un plan con Gemini y lo guarda en la base de datos."""
    if not GEMINI_API_KEY or not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY no configurada en el archivo .env"
        )

    prompt = f"""
    Crea un plan de estudio estructurado sobre el tema: "{solicitud.titulo}".
    - Nivel: {solicitud.nivel_objetivo}
    - Duración: {solicitud.duracion} días
    - Detalles adicionales: {solicitud.descripcion or 'Ninguno'}

    Responde EXCLUSIVAMENTE con un JSON válido sin formato markdown ni texto adicional:
    {{
      "resumen": "Descripción general",
      "modulos": [
        {{
          "dia": 1,
          "tema": "Título del módulo o tema",
          "detalles": "Detalle de actividades",
          "recursos": ["Recurso 1", "Recurso 2"]
        }}
      ]
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        contenido_json = json.loads(texto_limpio)
    except Exception as e:
        contenido_json = {
            "resumen": response.text if 'response' in locals() and hasattr(response, 'text') else "Plan genérico",
            "modulos": []
        }

    # Resolver id_asignatura si viene nulo para evitar violaciones de clave foránea
    id_asig = solicitud.id_asignatura
    if not id_asig:
        asig_existente = sesion.exec(select(Asignatura)).first()
        if asig_existente:
            id_asig = asig_existente.id_asignatura
        else:
            nueva_asig = Asignatura(
                nombre="General",
                descripcion="Asignatura general creada automáticamente",
                nivel_dificultad=solicitud.nivel_objetivo or "Intermedio"
            )
            sesion.add(nueva_asig)
            sesion.commit()
            sesion.refresh(nueva_asig)
    # Resolver y validar id_usuario en la base de datos
    user_db = sesion.get(Usuario, solicitud.id_usuario) if solicitud.id_usuario else None
    if not user_db:
        user_db = sesion.exec(select(Usuario)).first()
        if not user_db:
            user_db = Usuario(
                id_usuario=solicitud.id_usuario if solicitud.id_usuario else None,
                nombre="Estudiante StudNova",
                correo="estudiante@studnova.com",
                contraseña="123"
            )
            sesion.add(user_db)
            sesion.commit()
            sesion.refresh(user_db)
    id_user_valido = user_db.id_usuario

    nuevo_plan = PlanDeEstudio(
        id_usuario=id_user_valido,
        id_asignatura=id_asig,
        id_ruta=solicitud.id_ruta,
        titulo=solicitud.titulo,
        descripcion=solicitud.descripcion,
        nivel_objetivo=solicitud.nivel_objetivo,
        duracion=solicitud.duracion,
        estado="activo",
        contenido_json=contenido_json
    )

    sesion.add(nuevo_plan)
    sesion.commit()
    sesion.refresh(nuevo_plan)
    return nuevo_plan


@router.get("/", response_model=List[PlanDeEstudio])
def listar_todos_los_planes(sesion: Session = Depends(obtener_sesion)):
    """Lista todos los planes almacenados en la base de datos."""
    return sesion.exec(select(PlanDeEstudio)).all()


@router.get("/usuario/{id_usuario}", response_model=List[PlanDeEstudio])
def obtener_planes_usuario(id_usuario: int, sesion: Session = Depends(obtener_sesion)):
    """Obtiene los planes de un usuario ordenados del más reciente al más antiguo."""
    statement = (
        select(PlanDeEstudio)
        .where(PlanDeEstudio.id_usuario == id_usuario)
        .order_by(PlanDeEstudio.id_plan.desc())
    )
    return sesion.exec(statement).all()


@router.get("/{id_plan}")
def obtener_detalle_plan(id_plan: int, sesion: Session = Depends(obtener_sesion)):
    """Obtiene los detalles de un plan, soportando tanto estructura JSON como relacional."""
    plan = sesion.get(PlanDeEstudio, id_plan)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de estudio no encontrado"
        )

    modulos = sesion.exec(select(Modulo).where(Modulo.id_plan == id_plan)).all()

    estructura = []
    for mod in modulos:
        temas = sesion.exec(select(Tema).where(Tema.id_modulo == mod.id_modulo)).all()
        estructura.append({
            "modulo": mod,
            "temas": temas
        })

    contenido = plan.contenido_json
    if isinstance(contenido, str):
        try:
            contenido = json.loads(contenido)
        except json.JSONDecodeError:
            pass

    return {
        "plan": plan,
        "contenido_relacional": estructura,
        "contenido_json": contenido
    }


@router.post("/", response_model=PlanDeEstudio, status_code=status.HTTP_201_CREATED)
def crear_plan(plan: PlanDeEstudio, sesion: Session = Depends(obtener_sesion)):
    """Crea manualmente un plan de estudio."""
    sesion.add(plan)
    sesion.commit()
    sesion.refresh(plan)
    return plan


@router.put("/{id_plan}", response_model=PlanDeEstudio)
def actualizar_plan(id_plan: int, datos_plan: PlanDeEstudio, sesion: Session = Depends(obtener_sesion)):
    """Actualiza los campos de un plan existente."""
    plan_db = sesion.get(PlanDeEstudio, id_plan)
    if not plan_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de estudio no encontrado"
        )

    datos_dict = datos_plan.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        if key != "id_plan":
            setattr(plan_db, key, value)

    sesion.add(plan_db)
    sesion.commit()
    sesion.refresh(plan_db)
    return plan_db


@router.put("/{id_plan}/ajustar")
def ajustar_plan(id_plan: int, datos: PlanAjustarSchema, sesion: Session = Depends(obtener_sesion)):
    """Ajusta la estructura JSON de un plan existente utilizando Gemini según las indicaciones del usuario."""
    if not GEMINI_API_KEY or not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY no configurada en el archivo .env"
        )

    plan_db = sesion.get(PlanDeEstudio, id_plan)
    if not plan_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de estudio no encontrado"
        )

    prompt = f"""
    Ajusta el siguiente plan de estudio en formato JSON según estas indicaciones: "{datos.indicaciones}".

    Plan actual:
    {json.dumps(plan_db.contenido_json, ensure_ascii=False)}

    Responde EXCLUSIVAMENTE con el objeto JSON ajustado y actualizado sin bloques markdown.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        nuevo_contenido = json.loads(texto_limpio)

        plan_db.contenido_json = nuevo_contenido
        sesion.add(plan_db)
        sesion.commit()
        sesion.refresh(plan_db)

        return {
            "mensaje": f"Plan {id_plan} reajustado exitosamente por la IA.",
            "plan": plan_db
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reajustar el plan: {str(e)}"
        )


@router.delete("/{id_plan}", status_code=status.HTTP_200_OK)
def eliminar_plan(id_plan: int, sesion: Session = Depends(obtener_sesion)):
    """Elimina un plan de estudio por su ID."""
    plan_db = sesion.get(PlanDeEstudio, id_plan)
    if not plan_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de estudio no encontrado"
        )

    sesion.delete(plan_db)
    sesion.commit()
    return {"mensaje": f"Plan de estudio con ID {id_plan} eliminado correctamente."}