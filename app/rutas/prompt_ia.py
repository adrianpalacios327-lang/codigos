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
from app.modelos.asignatura import Asignatura
from app.modelos.usuario import Usuario

# Cargar variables de entorno
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

router = APIRouter(prefix="/prompt-ia", tags=["Asistente IA"])

# Valores estrictos permitidos por el tipo ENUM 'niveldificultad' en PostgreSQL
NIVELES_PERMITIDOS = ["Principiante", "Intermedio", "Avanzado"]


def validar_nivel_dificultad(nivel: str) -> str:
    """Garantiza que el nivel coincida con los valores permitidos en el ENUM de PostgreSQL."""
    if not nivel or nivel not in NIVELES_PERMITIDOS:
        return "Intermedio"  # Fallback seguro si recibe 'Personalizado' u otro valor invalido
    return nivel


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
         "nivel_dificultad": "Intermedio",
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
        # 1. Validar y resolver id_usuario en la base de datos
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
        id_usuario_valido = user_db.id_usuario

        # 2. Consultar el modelo de IA Gemini
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt_instrucciones
        )
        respuesta_raw = response.text.replace("```json", "").replace("```", "").strip()

        # CASO 1: Generación de plan de estudio
        if respuesta_raw.startswith("{") and "plan_generado" in respuesta_raw:
            datos_plan = json.loads(respuesta_raw)

            # Validar y sanitizar el nivel de dificultad para evitar error de ENUM
            nivel_recibido = datos_plan.get("nivel_dificultad", "Intermedio")
            nivel_validado = validar_nivel_dificultad(nivel_recibido)

            # Resolver id_asignatura para el nuevo plan
            asig_existente = sesion.exec(select(Asignatura)).first()
            id_asig = asig_existente.id_asignatura if asig_existente else None
            
            if not id_asig:
                # Extraer un nombre de asignatura limpio a partir del mensaje del usuario
                nombre_asig = solicitud.mensaje.lower()
                for prefijo in ["me das un plan de estudios de", "crea un plan de", "quiero aprender", "curso de", "plan de"]:
                    nombre_asig = nombre_asig.replace(prefijo, "")
                
                nombre_asig = nombre_asig.strip().title()
                if len(nombre_asig) > 40 or not nombre_asig:
                    nombre_asig = "General"

                nueva_asig = Asignatura(
                    nombre=nombre_asig,
                    descripcion="Asignatura generada automáticamente por StudNova IA",
                    nivel_dificultad=nivel_validado
                )
                sesion.add(nueva_asig)
                sesion.commit()
                sesion.refresh(nueva_asig)
                id_asig = nueva_asig.id_asignatura

            nuevo_plan = PlanDeEstudio(
                id_usuario=id_usuario_valido,
                id_asignatura=id_asig,
                titulo=datos_plan.get("titulo", f"Plan de {solicitud.mensaje[:30]}"),
                descripcion=datos_plan.get("resumen", "Plan generado con StudNova IA"),
                nivel_objetivo=nivel_validado,
                duracion=len(datos_plan.get("modulos", [])),
                estado="activo",
                contenido_json=datos_plan
            )
            sesion.add(nuevo_plan)
            sesion.commit()
            sesion.refresh(nuevo_plan)

            # Registrar la interacción en el historial
            registro_prompt = PromptIA(
                id_usuario=id_usuario_valido,
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
                select(PlanDeEstudio).where(PlanDeEstudio.id_usuario == id_usuario_valido)
            ).first()
            if primer_plan:
                plan_id = primer_plan.id_plan

        # Asignar id_usuario para trazabilidad completa
        registro_prompt = PromptIA(
            id_usuario=id_usuario_valido,
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
        # Sanitizar mensaje de error para evitar fallos de decodificacion en Windows
        error_limpio = str(e).encode('ascii', errors='ignore').decode('ascii')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servicio de IA: {error_limpio}"
        )


@router.get("/historial/{id_usuario}")
def obtener_historial(id_usuario: int, sesion: Session = Depends(obtener_sesion)):
    """Obtiene el historial de interacciones del usuario ordenado por fecha descendente."""
    statement = (
        select(PromptIA)
        .where(
            (PromptIA.id_usuario == id_usuario) |
            (PromptIA.id_plan.in_(
                select(PlanDeEstudio.id_plan).where(PlanDeEstudio.id_usuario == id_usuario)
            ))
        )
        .order_by(PromptIA.id_prompt.desc())
    )
    return sesion.exec(statement).all()


@router.get("/historial/plan/{id_plan}")
def obtener_historial_por_plan(id_plan: int, sesion: Session = Depends(obtener_sesion)):
    """Obtiene el historial de interacciones ligadas a un plan específico."""
    statement = select(PromptIA).where(PromptIA.id_plan == id_plan).order_by(PromptIA.id_prompt.desc())
    return sesion.exec(statement).all()


@router.get("/{id_prompt}", response_model=PromptIA)
def obtener_prompt_por_id(id_prompt: int, sesion: Session = Depends(obtener_sesion)):
    """Obtiene un registro específico del historial por su ID."""
    prompt = sesion.get(PromptIA, id_prompt)
    if not prompt:
        raise HTTPException(status_code=404, detail="Registro de interacción no encontrado.")
    return prompt


@router.put("/{id_prompt}", response_model=PromptIA)
def actualizar_prompt(id_prompt: int, datos_actualizar: PromptIA, sesion: Session = Depends(obtener_sesion)):
    """Actualiza un registro existente del historial."""
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
    """Elimina un registro del historial."""
    prompt_db = sesion.get(PromptIA, id_prompt)
    if not prompt_db:
        raise HTTPException(status_code=404, detail="Registro de interacción no encontrado.")

    sesion.delete(prompt_db)
    sesion.commit()
    return {"mensaje": f"Registro de historial {id_prompt} eliminado correctamente."}