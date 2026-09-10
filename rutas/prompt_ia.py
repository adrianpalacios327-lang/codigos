import os
import json
from dotenv import load_dotenv
from google import genai
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from base_datos import obtener_sesion
from app.esquemas.prompt_ia import ChatSolicitud
from app.modelos.prompt_ia import PromptIA
from app.modelos.plan_estudio import PlanDeEstudio

# Cargar variables de entorno
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

router = APIRouter(prefix="/prompt-ia", tags=["Asistente IA"])

@router.post("/chat", status_code=status.HTTP_201_CREATED)
def interactuar_ia(solicitud: ChatSolicitud, sesion: Session = Depends(obtener_sesion)):
    if not GEMINI_API_KEY or not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La API Key de Gemini no está configurada en las variables de entorno."
        )

    prompt_instrucciones = f"""
    Eres el asistente oficial de StudNova IA.
    Mensaje del usuario: "{solicitud.mensaje}"

    REGLAS DE RESPUESTA:
    1. Si el usuario te pide CREAR, GENERAR, HACER o ENSEÑAR un plan/curso/ruta de aprendizaje (ej: "crea un plan de matemáticas", "quiero aprender python"):
       Responde ÚNICAMENTE con este formato JSON exacto (sin bloques Markdown ```json, sin texto antes o después):
       {{
         "tipo": "plan_generado",
         "titulo": "Plan de {solicitud.mensaje[:30]}",
         "resumen": "Ruta de aprendizaje personalizada generada por StudNova IA.",
         "modulos": [
           {{
             "dia": 1,
             "tema": "Introducción y Conceptos Clave",
             "detalles": "Fundamentos iniciales y práctica guiada.",
             "recursos": ["Documentación oficial", "Ejercicios prácticos"]
           }}
         ]
       }}

    2. Si es una pregunta conceptual, saludo o duda general:
       Responde de forma natural en texto claro como tutor educativo.
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt_instrucciones
        )
        respuesta_raw = response.text.replace("```json", "").replace("```", "").strip()

        # CASO 1: Generación de plan de estudio
        if respuesta_raw.startswith("{") and "plan_generado" in respuesta_raw:
            datos_plan = json.loads(respuesta_raw)

            nuevo_plan = PlanDeEstudio(
                id_usuario=solicitud.id_usuario,
                titulo=datos_plan.get("titulo", f"Plan de {solicitud.mensaje[:30]}"),
                descripcion=datos_plan.get("resumen", "Plan generado con StudNova IA"),
                nivel_objetivo="Intermedio",
                duracion=len(datos_plan.get("modulos", [])),
                estado="activo",
                contenido_json=datos_plan
            )
            sesion.add(nuevo_plan)
            sesion.commit()
            sesion.refresh(nuevo_plan)

            # Registrar la interacción con el id_usuario correspondiente
            registro_prompt = PromptIA(
                id_usuario=solicitud.id_usuario,
                id_plan=nuevo_plan.id_plan,
                prompt_usuario=solicitud.mensaje,
                prompt_sistema=f"Plan de estudio generado exitosamente con ID {nuevo_plan.id_plan}"
            )
            sesion.add(registro_prompt)
            sesion.commit()

            return {
                "tipo": "plan_generado",
                "respuesta": f"✨ ¡He generado tu plan: '{nuevo_plan.titulo}'!",
                "plan": nuevo_plan
            }

        # CASO 2: Consulta conversacional o respuesta general
        plan_id = solicitud.id_plan
        if not plan_id:
            primer_plan = sesion.exec(
                select(PlanDeEstudio).where(PlanDeEstudio.id_usuario == solicitud.id_usuario)
            ).first()
            if primer_plan:
                plan_id = primer_plan.id_plan

        # Asignar id_usuario para evitar el NotNullViolation
        registro_prompt = PromptIA(
            id_usuario=solicitud.id_usuario,
            id_plan=plan_id,
            prompt_usuario=solicitud.mensaje,
            prompt_sistema=respuesta_raw
        )
        sesion.add(registro_prompt)
        sesion.commit()
        sesion.refresh(registro_prompt)

        return {
            "tipo": "texto",
            "respuesta": respuesta_raw,
            "registro": registro_prompt
        }

    except Exception as e:
        sesion.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servicio de IA: {str(e)}"
        )

@router.get("/historial/{id_usuario}")
def obtener_historial(id_usuario: int, sesion: Session = Depends(obtener_sesion)):
    statement = (
        select(PromptIA)
        .where(PromptIA.id_usuario == id_usuario)
    )
    return sesion.exec(statement).all()

@router.get("/historial/plan/{id_plan}")
def obtener_historial_por_plan(id_plan: int, sesion: Session = Depends(obtener_sesion)):
    statement = select(PromptIA).where(PromptIA.id_plan == id_plan)
    return sesion.exec(statement).all()

@router.get("/{id_prompt}", response_model=PromptIA)
def obtener_prompt_por_id(id_prompt: int, sesion: Session = Depends(obtener_sesion)):
    prompt = sesion.get(PromptIA, id_prompt)
    if not prompt:
        raise HTTPException(status_code=404, detail="Registro de interacción no encontrado.")
    return prompt

@router.put("/{id_prompt}", response_model=PromptIA)
def actualizar_prompt(id_prompt: int, datos_actualizar: PromptIA, sesion: Session = Depends(obtener_sesion)):
    prompt_db = sesion.get(PromptIA, id_prompt)
    if not prompt_db:
        raise HTTPException(status_code=404, detail="Registro de interacción no encontrado.")
    
    datos_dict = datos_actualizar.model_dump(exclude_unset=True)
    for key, value in datos_dict.items():
        if key != "id_prompt":
            setattr(prompt_db, key, value)
            
    sesion.add(prompt_db)
    sesion.commit()
    sesion.refresh(prompt_db)
    return prompt_db

@router.delete("/{id_prompt}", status_code=status.HTTP_200_OK)
def eliminar_prompt(id_prompt: int, sesion: Session = Depends(obtener_sesion)):
    prompt_db = sesion.get(PromptIA, id_prompt)
    if not prompt_db:
        raise HTTPException(status_code=404, detail="Registro de interacción no encontrado.")
    
    sesion.delete(prompt_db)
    sesion.commit()
    return {"mensaje": f"Registro de historial {id_prompt} eliminado correctamente."}