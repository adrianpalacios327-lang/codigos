from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import uuid
import json
import re
import unicodedata
from sqlmodel import Session, select
from base_datos import obtener_sesion
from app.gemini import generar_codigo_ia, obtener_embedding, calcular_similitud_coseno
from app.utilidades.extractor_texto import extraer_texto_de_archivo
from app.modelos.usuario import Usuario
from app.modelos.asignatura import Asignatura
from app.modelos.plan_estudio import PlanDeEstudio
from app.modelos.modulo import Modulo
from app.modelos.tema import Tema
from app.modelos.prompt_ia import PromptIA

router = APIRouter(prefix="/api/ia", tags=["IA Generador"])

# Modelo para los mensajes previos del chat
class MensajeHistorial(BaseModel):
    rol: str   # "usuario" o "ia"
    texto: str

# Modelo de solicitud con memoria de conversación
class SolicitudGeneracion(BaseModel):
    prompt: str
    id_usuario: Optional[int] = None
    historial: Optional[List[MensajeHistorial]] = []
    forzar_nuevo: Optional[bool] = False

class SolicitudAceptarPlan(BaseModel):
    id_plan: int
    id_usuario: Optional[int] = None

def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto

def extraer_palabras_clave(texto: str) -> set:
    t = normalizar_texto(texto)
    stopwords = {
        'hola', 'buenas', 'buenos', 'dias', 'tardes', 'noches', 'que', 'tal', 'como', 'estas', 'esta', 'estoy', 'estan', 'estamos',
        'por', 'favor', 'quiero', 'necesito', 'gustaria', 'aprender', 'estudiar', 'saber', 'ensenar', 'ensename',
        'crea', 'crear', 'creame', 'generar', 'generame', 'haz', 'hazme', 'dame', 'un', 'una', 'unos', 'unas',
        'el', 'la', 'los', 'las', 'de', 'del', 'en', 'para', 'sobre', 'con', 'desde', 'cero', 'ed',
        'plan', 'estudio', 'estudios', 'ruta', 'aprendizaje', 'curso', 'tutorial', 'guia', 'temario',
        'semana', 'semanas', 'mes', 'meses', 'dia', 'dias', 'hora', 'horas', 'modulo', 'modulos', 'moudulo', 'moudulos',
        'nivel', 'basico', 'intermedio', 'avanzado', 'principiante', 'principiantes', 'intensivo',
        'te', 'me', 'se', 'nos', 'le', 'les', 'lo', 'va', 'van', 'vas', 'voy', 'fue', 'era', 'soy', 'eres', 'es', 'somos', 'son',
        'bien', 'mal', 'mas', 'menos', 'muy', 'tan', 'tanto', 'hacer', 'haces', 'hace', 'dice', 'dices', 'decir',
        'ver', 'ves', 'mira', 'oye', 'amigo', 'amiga', 'amor', 'adios', 'chao', 'gracias', 'denada', 'ok', 'okay', 'vale',
        'si', 'no', 'cual', 'quien', 'donde', 'cuando', 'porque', 'por que', 'algo', 'nada', 'todo', 'todos', 'todas',
        'otro', 'otra', 'otros', 'otras', 'nuevo', 'nueva', 'nuevos', 'nuevas', 'cambiar', 'cambio', 'tema', 'temas',
        'tiempo', 'dividido', 'detalles', 'ejercicios', 'practica', 'practico', 'practicos'
    }
    palabras = [p for p in re.findall(r'[a-z0-9+#]+', t) if not p.isdigit()]
    tecnologias_cortas = {'c', 'r', 'js', 'ai', 'ui', 'ux', 'go', 'db', 'ml', 'qa'}
    return {p for p in palabras if p not in stopwords and (len(p) > 2 or p in tecnologias_cortas)}

def buscar_plan_en_cache(sesion: Session, texto_consulta: str, usuario_id: Optional[int] = None, umbral_similitud: float = 0.85):
    """
    Busca si ya existe un plan de estudio en la BD que coincida semánticamente
    y por materia/palabras clave con la petición del usuario, para evitar llamar a Gemini y ahorrar tokens.
    """
    texto_limpio = texto_consulta.strip()
    if len(texto_limpio) < 3:
        return None

    # Frases comunes de saludo y conversación que NUNCA deben disparar búsqueda de plan
    saludos_simples = {
        "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches",
        "que tal", "como estas", "como te va", "como vas", "que haces",
        "como te encuentras", "ok", "gracias", "si", "no", "bien", "genial",
        "hola amor", "cambiar de tema", "que cuentas"
    }
    if normalizar_texto(texto_limpio) in saludos_simples:
        return None

    kw_usuario = extraer_palabras_clave(texto_limpio)
    # Si la consulta no tiene palabras temáticas relevantes, no es una solicitud de plan
    if not kw_usuario:
        return None

    mejor_plan = None
    max_similitud = 0.0

    # 1. Búsqueda directa en planes de estudio existentes (estrictamente por TÍTULO y MATERIA)
    planes = sesion.exec(
        select(PlanDeEstudio).where(PlanDeEstudio.contenido_json != None)
    ).all()

    for p in planes:
        materia = ""
        if isinstance(p.contenido_json, dict):
            materia = p.contenido_json.get("materia", "")
        # Solo comparar título y materia (el núcleo del tema), para evitar falsos positivos con palabras de la descripción
        texto_comparar = f"{p.titulo or ''} {materia}"
        kw_plan = extraer_palabras_clave(texto_comparar)

        interseccion = kw_usuario.intersection(kw_plan)
        if interseccion:
            ratio = len(interseccion) / max(len(kw_usuario), 1)
            if ratio >= 0.5 or any(len(palabra) >= 4 for palabra in interseccion):
                mejor_plan = p
                max_similitud = 1.0
                break

    # 2. Búsqueda por Asignatura registrada en BD
    if not mejor_plan:
        asignaturas = sesion.exec(select(Asignatura)).all()
        for asig in asignaturas:
            if not asig.nombre or asig.nombre.lower() in ("string", "general", "personalizado", "prueba"):
                continue
            asig_norm = normalizar_texto(asig.nombre)
            asig_kw = extraer_palabras_clave(asig.nombre)
            
            if (asig_norm and asig_norm in normalizar_texto(texto_limpio)) or (asig_kw and bool(asig_kw.intersection(kw_usuario))):
                plan_asig = sesion.exec(
                    select(PlanDeEstudio)
                    .where(PlanDeEstudio.id_asignatura == asig.id_asignatura)
                    .where(PlanDeEstudio.contenido_json != None)
                ).first()
                if plan_asig and plan_asig.contenido_json:
                    mejor_plan = plan_asig
                    max_similitud = 1.0
                    break

    # 3. Búsqueda por Embeddings semánticos
    if not mejor_plan:
        emb_actual = obtener_embedding(texto_limpio)
        if emb_actual:
            prompts_previos = sesion.exec(
                select(PromptIA)
                .where(PromptIA.id_plan != None)
                .where(PromptIA.embedding != None)
            ).all()

            for p in prompts_previos:
                try:
                    emb_guardado = json.loads(p.embedding)
                    sim = calcular_similitud_coseno(emb_actual, emb_guardado)
                    if sim >= umbral_similitud and sim > max_similitud:
                        plan_asociado = sesion.get(PlanDeEstudio, p.id_plan)
                        if plan_asociado and plan_asociado.contenido_json:
                            materia_plan = str(plan_asociado.contenido_json.get("materia", "")) if isinstance(plan_asociado.contenido_json, dict) else ""
                            kw_plan = extraer_palabras_clave(f"{plan_asociado.titulo} {materia_plan} {p.prompt_usuario}")
                            
                            if kw_usuario and not (kw_usuario.intersection(kw_plan)):
                                continue

                            mejor_plan = plan_asociado
                            max_similitud = sim
                except Exception as e:
                    print(f"⚠️ Error al leer embedding de prompt {p.id_prompt}: {e}")
                    continue

    # 4. Si encontramos un plan reutilizable, retornarlo
    if mejor_plan and mejor_plan.contenido_json:
        contenido = mejor_plan.contenido_json
        if isinstance(contenido, str):
            try:
                contenido = json.loads(contenido)
            except Exception:
                pass
        return {
            "tipo": "plan_generado",
            "mensaje": f"⚡ ¡He encontrado un plan de estudio ya preparado sobre {mejor_plan.titulo}!",
            "plan": contenido,
            "id_plan": mejor_plan.id_plan,
            "id_usuario": usuario_id or mejor_plan.id_usuario,
            "desde_cache": True,
            "similitud": round(max_similitud, 3)
        }

    return None


def normalizar_a_dict(obj):
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        return {"titulo": str(obj), "modulos": []}
    return {}


def guardar_plan_generado_en_bd(sesion: Session, usuario_id: int, prompt_texto: str, resultado: dict) -> dict:
    """Guarda el plan generado, módulos, temas, embedding y registro de PromptIA en la base de datos."""
    if not isinstance(resultado, dict):
        return {"tipo": "error", "mensaje": "Respuesta no válida del generador"}

    plan_raw = resultado.get("plan")
    if not plan_raw:
        plan_raw = resultado
    plan_data = normalizar_a_dict(plan_raw)

    # Obtener o crear asignatura
    nombre_materia = plan_data.get("materia") or "General"
    if not isinstance(nombre_materia, str):
        nombre_materia = str(nombre_materia)

    asignatura_db = sesion.exec(select(Asignatura).where(Asignatura.nombre == nombre_materia)).first()
    if not asignatura_db:
        asignatura_db = Asignatura(
            nombre=nombre_materia,
            descripcion=f"Asignatura de {nombre_materia} generada por IA",
            nivel_dificultad="Personalizado"
        )
        sesion.add(asignatura_db)
        sesion.commit()
        sesion.refresh(asignatura_db)

    # Guardar el nuevo Plan de Estudio
    titulo_plan = plan_data.get("titulo") or "Plan de Estudio Personalizado"
    if not isinstance(titulo_plan, str):
        titulo_plan = str(titulo_plan)

    descripcion_plan = plan_data.get("descripcion") or ""
    if not isinstance(descripcion_plan, str):
        descripcion_plan = str(descripcion_plan)

    nuevo_plan = PlanDeEstudio(
        id_usuario=usuario_id,
        id_asignatura=asignatura_db.id_asignatura,
        titulo=titulo_plan,
        descripcion=descripcion_plan,
        estado="activo",
        contenido_json=plan_data
    )
    sesion.add(nuevo_plan)
    sesion.commit()
    sesion.refresh(nuevo_plan)

    # Guardar Módulos y Temas
    plan_data["id_plan"] = nuevo_plan.id_plan
    modulos_list = plan_data.get("modulos", [])
    if not isinstance(modulos_list, list):
        modulos_list = []

    for idx_m, mod in enumerate(modulos_list):
        if not isinstance(mod, dict):
            if isinstance(mod, str):
                mod = {"titulo": mod, "teoria_modulo": mod, "lecciones": []}
            else:
                mod = {"titulo": f"Módulo {idx_m + 1}", "lecciones": []}
            modulos_list[idx_m] = mod

        nuevo_modulo = Modulo(
            id_plan=nuevo_plan.id_plan,
            nombre=str(mod.get("titulo") or f"Módulo {idx_m + 1}"),
            descripcion=str(mod.get("teoria_modulo") or ""),
            numero_modulo=idx_m + 1,
            objetivo=str(mod.get("nivel_tag") or "Objetivo del módulo"),
            estado="activo"
        )
        sesion.add(nuevo_modulo)
        sesion.commit()
        sesion.refresh(nuevo_modulo)
        mod["id_modulo"] = nuevo_modulo.id_modulo

        lecciones_list = mod.get("lecciones", [])
        if not isinstance(lecciones_list, list):
            lecciones_list = []

        for idx_t, lec in enumerate(lecciones_list):
            if not isinstance(lec, dict):
                if isinstance(lec, str):
                    lec = {"titulo": lec, "concepto_teorico": lec}
                else:
                    lec = {"titulo": f"Lección {idx_t + 1}"}
                lecciones_list[idx_t] = lec

            nuevo_tema = Tema(
                id_modulo=nuevo_modulo.id_modulo,
                nombre=str(lec.get("titulo") or f"Lección {idx_t + 1}"),
                descripcion=str(lec.get("concepto_teorico") or ""),
                numero_tema=idx_t + 1,
                duracion_estimada=int(lec.get("duracion_minutos") or 45)
            )
            sesion.add(nuevo_tema)
            sesion.commit()
            sesion.refresh(nuevo_tema)
            lec["id_tema"] = nuevo_tema.id_tema

    plan_data["modulos"] = modulos_list
    nuevo_plan.contenido_json = plan_data
    sesion.add(nuevo_plan)
    sesion.commit()

    # Generar embedding del prompt para el caché semántico futuro
    texto_para_embedding = f"{prompt_texto} {nombre_materia} {nuevo_plan.titulo}"
    vector_embedding = obtener_embedding(texto_para_embedding)

    registro_prompt = PromptIA(
        id_usuario=usuario_id,
        id_plan=nuevo_plan.id_plan,
        prompt_usuario=prompt_texto,
        prompt_sistema=resultado.get("mensaje") or "Plan generado",
        modelo_ia=resultado.get("modelo_ia", "gemini/gemini-3.5-flash-lite"),
        embedding=json.dumps(vector_embedding) if vector_embedding else None,
        estado="completado"
    )
    sesion.add(registro_prompt)
    sesion.commit()

    resultado["id_plan"] = nuevo_plan.id_plan
    resultado["id_usuario"] = usuario_id
    resultado["plan"] = plan_data
    resultado["desde_cache"] = False
    return resultado


@router.post("/generar")
def generar_interfaz(solicitud: SolicitudGeneracion, sesion: Session = Depends(obtener_sesion)):
    if not solicitud.prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")
    
    try:
        usuario_id = solicitud.id_usuario
        usuario_db = sesion.get(Usuario, usuario_id) if usuario_id else None
        if not usuario_db:
            usuario_db = sesion.exec(select(Usuario)).first()
            if not usuario_db:
                usuario_db = Usuario(
                    id_usuario=usuario_id if usuario_id else None,
                    nombre="Estudiante StudNova",
                    correo="estudiante@studnova.com",
                    contraseña="123"
                )
                sesion.add(usuario_db)
                sesion.commit()
                sesion.refresh(usuario_db)
            usuario_id = usuario_db.id_usuario

        # 1. VERIFICAR SI YA EXISTE UN PLAN SIMILAR (Ahorro de tokens)
        # Si el usuario NO forzó la creación de uno nuevo, sugerir el plan existente
        if not getattr(solicitud, "forzar_nuevo", False):
            plan_existente = buscar_plan_en_cache(sesion, solicitud.prompt, usuario_id)
            if plan_existente and isinstance(plan_existente, dict) and plan_existente.get("plan"):
                plan_obj = plan_existente["plan"]
                if isinstance(plan_obj, str):
                    try:
                        plan_obj = json.loads(plan_obj)
                    except Exception:
                        plan_obj = {"titulo": plan_obj}
                if not isinstance(plan_obj, dict):
                    plan_obj = {"titulo": str(plan_obj)}

                titulo_plan = plan_obj.get("titulo") or "Plan de Estudio"
                return {
                    "tipo": "sugerencia_plan_existente",
                    "mensaje": f"💡 Ya existe en nuestra biblioteca un plan de estudio sobre **{titulo_plan}**.",
                    "plan_sugerido": plan_obj,
                    "id_plan": plan_existente.get("id_plan"),
                    "prompt_original": solicitud.prompt,
                    "similitud": plan_existente.get("similitud", 1.0)
                }

        nombre_vista = f"vista_{uuid.uuid4().hex[:8]}"
        historial_dicts = [m.model_dump() for m in solicitud.historial]
        
        resultado = generar_codigo_ia(
            prompt_usuario=solicitud.prompt,
            historial=historial_dicts,
            nombre_archivo=nombre_vista
        )

        if isinstance(resultado, str):
            try:
                resultado = json.loads(resultado)
            except Exception:
                resultado = {"tipo": "conversacion", "mensaje": resultado}

        if not isinstance(resultado, dict):
            resultado = {"tipo": "conversacion", "mensaje": str(resultado)}

        tiene_plan = (resultado.get("tipo") == "plan_generado") or ("plan" in resultado) or ("modulos" in resultado)
        if tiene_plan and (resultado.get("plan") or resultado.get("modulos")):
            if "plan" not in resultado:
                resultado = {"tipo": "plan_generado", "mensaje": "Plan generado con éxito", "plan": resultado}
            resultado = guardar_plan_generado_en_bd(sesion, usuario_id, solicitud.prompt, resultado)
        
        return resultado
        
    except Exception as e:
        sesion.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/aceptar-sugerencia")
def aceptar_sugerencia(solicitud: SolicitudAceptarPlan, sesion: Session = Depends(obtener_sesion)):
    """Permite al usuario adoptar un plan de estudio ya existente ahorrando el 100% de tokens de IA."""
    try:
        plan_origen = sesion.get(PlanDeEstudio, solicitud.id_plan)
        if not plan_origen or not plan_origen.contenido_json:
            raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")

        usuario_id = solicitud.id_usuario
        if not usuario_id:
            usuario_db = sesion.exec(select(Usuario)).first()
            usuario_id = usuario_db.id_usuario if usuario_db else 1

        contenido_plan = plan_origen.contenido_json
        if isinstance(contenido_plan, str):
            try:
                contenido_plan = json.loads(contenido_plan)
            except Exception:
                pass

        # Si el plan ya pertenece a este usuario, devolverlo directamente
        if plan_origen.id_usuario == usuario_id:
            return {
                "tipo": "plan_generado",
                "mensaje": f"⚡ ¡Cargando tu plan existente: '{plan_origen.titulo}'!",
                "plan": contenido_plan,
                "id_plan": plan_origen.id_plan,
                "id_usuario": usuario_id,
                "desde_cache": True
            }

        # Si pertenece a otro usuario o general, vincularlo/clonarlo para este usuario
        nuevo_plan = PlanDeEstudio(
            id_usuario=usuario_id,
            id_asignatura=plan_origen.id_asignatura,
            titulo=plan_origen.titulo,
            descripcion=plan_origen.descripcion,
            nivel_objetivo=plan_origen.nivel_objetivo,
            duracion=plan_origen.duracion,
            estado="activo",
            contenido_json=contenido_plan
        )
        sesion.add(nuevo_plan)
        sesion.commit()
        sesion.refresh(nuevo_plan)

        if isinstance(contenido_plan, dict):
            contenido_plan["id_plan"] = nuevo_plan.id_plan
            nuevo_plan.contenido_json = contenido_plan
            sesion.add(nuevo_plan)
            sesion.commit()

        # Registrar prompt de trazabilidad sin consumir tokens
        registro_prompt = PromptIA(
            id_usuario=usuario_id,
            id_plan=nuevo_plan.id_plan,
            prompt_usuario=f"Adoptó plan sugerido: {nuevo_plan.titulo}",
            prompt_sistema=f"Plan adoptado de ID {plan_origen.id_plan}",
            modelo_ia="cache/plan-existente",
            estado="completado"
        )
        sesion.add(registro_prompt)
        sesion.commit()

        return {
            "tipo": "plan_generado",
            "mensaje": f"✨ ¡Has agregado a tu biblioteca el plan: '{nuevo_plan.titulo}'!",
            "plan": contenido_plan,
            "id_plan": nuevo_plan.id_plan,
            "id_usuario": usuario_id,
            "desde_cache": True
        }

    except HTTPException:
        raise
    except Exception as e:
        sesion.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generar-con-archivo")
async def generar_con_archivo(
    prompt: str = Form("Genera un plan de estudio a partir de este documento."),
    id_usuario: Optional[int] = Form(None),
    cantidad_modulos: Optional[int] = Form(None),
    duracion_personalizada: Optional[str] = Form(None),
    historial_json: Optional[str] = Form(None),
    archivo: Optional[UploadFile] = File(None),
    forzar_nuevo: Optional[bool] = Form(False),
    sesion: Session = Depends(obtener_sesion)
):
    try:
        usuario_id = id_usuario
        usuario_db = sesion.get(Usuario, usuario_id) if usuario_id else None
        if not usuario_db:
            usuario_db = sesion.exec(select(Usuario)).first()
            if not usuario_db:
                usuario_db = Usuario(
                    id_usuario=usuario_id if usuario_id else None,
                    nombre="Estudiante StudNova",
                    correo="estudiante@studnova.com",
                    contraseña="123"
                )
                sesion.add(usuario_db)
                sesion.commit()
                sesion.refresh(usuario_db)
            usuario_id = usuario_db.id_usuario

        texto_extraido = ""
        nombre_doc = ""
        if archivo and archivo.filename:
            nombre_doc = archivo.filename
            contenido_bytes = await archivo.read()
            if contenido_bytes:
                texto_extraido = extraer_texto_de_archivo(contenido_bytes, nombre_doc)

        # Si no hay documento adjunto y no se forzó nuevo, verificar si existe plan similar en la base de datos
        if not texto_extraido and not nombre_doc and not forzar_nuevo:
            plan_existente = buscar_plan_en_cache(sesion, prompt, usuario_id)
            if plan_existente and isinstance(plan_existente, dict) and plan_existente.get("plan"):
                plan_obj = plan_existente["plan"]
                if isinstance(plan_obj, str):
                    try:
                        plan_obj = json.loads(plan_obj)
                    except Exception:
                        plan_obj = {"titulo": plan_obj}
                if not isinstance(plan_obj, dict):
                    plan_obj = {"titulo": str(plan_obj)}

                titulo_plan = plan_obj.get("titulo") or "Plan de Estudio"
                return {
                    "tipo": "sugerencia_plan_existente",
                    "mensaje": f"💡 Ya existe en nuestra biblioteca un plan de estudio sobre **{titulo_plan}**.",
                    "plan_sugerido": plan_obj,
                    "id_plan": plan_existente.get("id_plan"),
                    "prompt_original": prompt,
                    "similitud": plan_existente.get("similitud", 1.0)
                }

        historial_dicts = []
        if historial_json:
            try:
                historial_dicts = json.loads(historial_json)
            except Exception:
                historial_dicts = []

        nombre_vista = f"vista_{uuid.uuid4().hex[:8]}"
        prompt_final = prompt
        if nombre_doc and not texto_extraido:
            prompt_final += f" (Archivo adjunto: {nombre_doc})"

        resultado = generar_codigo_ia(
            prompt_usuario=prompt_final,
            historial=historial_dicts,
            nombre_archivo=nombre_vista,
            texto_documento=texto_extraido if texto_extraido else None,
            cantidad_modulos=cantidad_modulos,
            duracion_personalizada=duracion_personalizada
        )

        if isinstance(resultado, str):
            try:
                resultado = json.loads(resultado)
            except Exception:
                resultado = {"tipo": "conversacion", "mensaje": resultado}

        if not isinstance(resultado, dict):
            resultado = {"tipo": "conversacion", "mensaje": str(resultado)}

        tiene_plan = (resultado.get("tipo") == "plan_generado") or ("plan" in resultado) or ("modulos" in resultado)
        if tiene_plan and (resultado.get("plan") or resultado.get("modulos")):
            if "plan" not in resultado:
                resultado = {"tipo": "plan_generado", "mensaje": "Plan generado con éxito", "plan": resultado}
            resultado = guardar_plan_generado_en_bd(sesion, usuario_id, prompt_final, resultado)
            if nombre_doc:
                resultado["archivo_procesado"] = nombre_doc
        
        return resultado

    except Exception as e:
        sesion.rollback()
        raise HTTPException(status_code=500, detail=str(e))
