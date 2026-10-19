from pathlib import Path
import os
import json
import re
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError

import math

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")

MODELOS_CASCADA = [
    "gemini-flash-lite-latest"
]

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GEMINI_API_KEY en las variables de entorno o en el archivo .env")
    return genai.Client(api_key=api_key)


def calcular_similitud_coseno(vec_a: list, vec_b: list) -> float:
    """Calcula la similitud de coseno entre dos vectores numéricos (0.0 a 1.0)."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def obtener_embedding(texto: str) -> list:
    """Genera el embedding vectorial del texto utilizando el modelo oficial gemini-embedding-001."""
    if not texto or not texto.strip():
        return []
    try:
        client = get_gemini_client()
        resultado = client.models.embed_content(
            model="gemini-embedding-001",
            contents=texto.strip()
        )
        if resultado and resultado.embeddings:
            return resultado.embeddings[0].values
    except Exception as e:
        print(f"[IA Embeddings] Error al generar embedding: {e}")
    return []


# PROMPT DINÁMICO, PEDAGÓGICO Y MULTIMODULAR
PROMPT_TUTOR_PROFUNDO = """
Eres el tutor pedagógico inteligente y cercano de StudNova IA.
Tu objetivo es conversar de forma natural, empática y dinámica con el estudiante para estructurar su aprendizaje de forma personalizada.

REGLAS DE CONVERSACIÓN (¡OBLIGATORIAS!):
1. ¡NUNCA repitas el mismo mensaje de saludo en cada turno! Habla como un tutor humano cálido y motivador.
2. SI EL ESTUDIANTE INDICA UN TEMA O SOLICITA UN NUEVO PLAN (ej: "álgebra", "quiero aprender python", "crear un nuevo plan"):
   - NO generes el plan de inmediato si aún no tienes el tiempo disponible o la cantidad de módulos.
   - Responde con "tipo": "conversacion" mostrando entusiasmo por el tema y pregúntale amablemente:
     a) ¿En cuánto tiempo planea estudiarlo o completarlo? (ej: 2 semanas, 1 mes).
     b) ¿En cuántos módulos desea dividirlo? (recomiéndale entre 3 y 6 módulos para un progreso estructurado).
3. CUÁNDO GENERAR EL PLAN ("tipo": "plan_generado"):
   - ÚNICAMENTE genera el plan cuando el estudiante haya respondido o definido el tiempo estimado O la cantidad de módulos que desea.
   - O si el estudiante adjuntó un documento temario explícito.
4. REGLA ESTRICTA DE MÓDULOS:
   - Un plan de estudio NUNCA debe contener un solo módulo, a menos que el usuario lo pida expresamente.
   - Si el usuario solicitó N módulos, genera EXACTAMENTE N módulos bien diferenciados.
   - Si no especificó un número exacto pero ya dio el tiempo, genera por defecto entre 3 y 4 módulos progresivos (Fundamentos -> Profundización -> Aplicación Práctica).

ESTRUCTURA DE RESPUESTA EN JSON PURO:

CASO 1: MIENTRAS ESTÉS CONVERSANDO O PIDIENDO DETALLES DE TIEMPO / MÓDULOS:
{
  "tipo": "conversacion",
  "mensaje": "Escribe aquí tu respuesta empática, preguntando el tiempo y número de módulos que desea el estudiante."
}

CASO 2: CUANDO YA TENGAS LOS PARÁMETROS Y GENERES EL PLAN COMPLETO:
{
  "tipo": "plan_generado",
  "mensaje": "¡Excelente! He estructurado tu plan de estudio personalizado para [Materia] en [X tiempo] distribuido en [N] módulos:",
  "plan": {
    "titulo": "Título atractivo y profesional del plan",
    "descripcion": "Objetivos pedagógicos del plan de estudio.",
    "materia": "Materia o tecnología",
    "recomendacion_fatiga": "Estudia 25 min y descansa 5 min para consolidar la memoria.",
    "modulos": [
      {
        "id": "mod-1",
        "nivel_tag": "Nivel 1: Fundamentos",
        "nivel_clase": "basico",
        "titulo": "Nombre del Módulo 1",
        "teoria_modulo": "Marco teórico del módulo explicando los conceptos fundamentales.",
        "lecciones": [
          {
            "titulo": "Nombre de la lección",
            "duracion_minutos": 45,
            "concepto_teorico": "Explicación conceptual profunda, didáctica y clara (mínimo 2 párrafos).",
            "puntos_clave": [
              "Regla o principio clave 1.",
              "Regla o principio clave 2."
            ],
            "ejemplo_codigo_o_formula": "Código real comentado o fórmula explicada paso a paso.",
            "ejercicio_practico": {
              "enunciado": "Problema práctico que el estudiante debe resolver.",
              "solucion_paso_a_paso": "Paso 1... Paso 2... Solución final explicada."
            }
          }
        ],
        "mini_quizzes": [
          {
            "titulo": "Comprobación de Concepto",
            "pregunta": "¿Pregunta conceptual clave?",
            "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
            "indice_correcto": 0,
            "explicacion": "Explicación de la respuesta."
          }
        ]
      },
      {
        "id": "mod-2",
        "nivel_tag": "Nivel 2: Profundización y Métodos",
        "nivel_clase": "intermedio",
        "titulo": "Nombre del Módulo 2",
        "teoria_modulo": "Marco teórico intermedio y métodos prácticos.",
        "lecciones": [
          {
            "titulo": "Nombre de la lección intermedia",
            "duracion_minutos": 50,
            "concepto_teorico": "Explicación técnica y práctica intermedia.",
            "puntos_clave": ["Punto clave intermedio 1", "Punto clave intermedio 2"],
            "ejemplo_codigo_o_formula": "Ejemplo intermedio aplicado.",
            "ejercicio_practico": {
              "enunciado": "Ejercicio práctico intermedio.",
              "solucion_paso_a_paso": "Solución paso a paso."
            }
          }
        ],
        "mini_quizzes": [
          {
            "titulo": "Comprobación de Concepto 2",
            "pregunta": "¿Pregunta del módulo 2?",
            "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
            "indice_correcto": 0,
            "explicacion": "Explicación."
          }
        ]
      },
      {
        "id": "mod-3",
        "nivel_tag": "Nivel 3: Aplicación Avanzada y Proyectos",
        "nivel_clase": "avanzado",
        "titulo": "Nombre del Módulo 3",
        "teoria_modulo": "Integración y aplicaciones reales del conocimiento adquirido.",
        "lecciones": [
          {
            "titulo": "Nombre de la lección avanzada",
            "duracion_minutos": 60,
            "concepto_teorico": "Explicación avanzada orientada a soluciones reales.",
            "puntos_clave": ["Punto avanzado 1", "Punto avanzado 2"],
            "ejemplo_codigo_o_formula": "Proyecto o caso real integrado.",
            "ejercicio_practico": {
              "enunciado": "Reto práctico integrador.",
              "solucion_paso_a_paso": "Solución detallada."
            }
          }
        ],
        "mini_quizzes": [
          {
            "titulo": "Comprobación de Concepto 3",
            "pregunta": "¿Pregunta del módulo avanzado?",
            "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
            "indice_correcto": 0,
            "explicacion": "Explicación."
          }
        ]
      }
    ]
  }
}
"""

def generar_codigo_ia(
    prompt_usuario: str,
    historial: list = None,
    nombre_archivo: str = "plan_estudio",
    texto_documento: str = None,
    cantidad_modulos: int = None,
    duracion_personalizada: str = None
):
    if historial is None:
        historial = []

    # Construir bloque de documento y especificaciones personalizadas
    bloque_documento = ""
    if texto_documento and texto_documento.strip():
        bloque_documento = f"""
DOCUMENTO / TEMARIO ADJUNTO POR EL ESTUDIANTE:
--------------------------------------------------
{texto_documento.strip()}
--------------------------------------------------
INSTRUCCIÓN OBLIGATORIA DEL DOCUMENTO:
Debes estructurar el plan de estudio basándote FIELMENTE en los temas, capítulos y conceptos de este documento adjunto. Genera directamente el plan pedagógico con "tipo": "plan_generado".
"""

    bloque_restricciones = ""
    if cantidad_modulos and int(cantidad_modulos) > 0:
        bloque_restricciones += f"\n- REQUISITO ESTRICTO DE MÓDULOS: El plan DEBE contener EXACTAMENTE {cantidad_modulos} módulos (ni más ni menos). Cada módulo debe tener lecciones completas y mini quizzes."
    else:
        bloque_restricciones += "\n- REQUISITO GENERAL DE MÓDULOS: Si vas a generar el plan, este DEBE tener entre 3 y 5 módulos progresivos y completos (NUNCA generes solo 1 módulo)."

    if duracion_personalizada and str(duracion_personalizada).strip():
        bloque_restricciones += f"\n- REQUISITO ESTRICTO DE TIEMPO: El plan debe estructurarse para completarse en {str(duracion_personalizada).strip()}."

    # -------------------------------------------------------------
    # 1. INTENTAR CON GEMINI (1ª OPCIÓN: gemini-flash-lite-latest)
    # -------------------------------------------------------------
    conversacion_texto = ""
    for msg in historial:
        rol = "Estudiante" if msg.get("rol") == "usuario" else "Tutor StudNova"
        conversacion_texto += f"{rol}: {msg.get('texto')}\n"

    conversacion_texto += f"Estudiante: {prompt_usuario}\n"

    # Control de acción: solo genera directo si hay documento o si ya se especificaron módulos y tiempo
    if bloque_documento or (cantidad_modulos and duracion_personalizada):
        instruccion_accion = "El estudiante ya proporcionó los parámetros necesarios o adjuntó un documento. GENERA DIRECTAMENTE el plan completo con 'tipo': 'plan_generado' cumpliendo la cantidad de módulos solicitada."
    else:
        instruccion_accion = "Lee atentamente el historial. Si el estudiante recién menciona el tema o solicitó un nuevo plan pero NO ha indicado la duración o los módulos deseados, RESPONDE CON 'tipo': 'conversacion' y pregúntale ambos datos antes de generar el plan. Si ya indicó ambos datos en los mensajes, genera el plan con 'tipo': 'plan_generado' con al menos 3 módulos."

    prompt_completo = f"""
INSTRUCCIONES DEL TUTOR STUDNOVA:
{PROMPT_TUTOR_PROFUNDO}
{bloque_documento}
{bloque_restricciones}

HISTORIAL DE LA CONVERSACIÓN ACUMULADA:
{conversacion_texto}

INSTRUCCIÓN ESPECÍFICA PARA ESTE TURNO:
{instruccion_accion}

Responde ÚNICAMENTE con JSON válido:
"""

    ultimo_error_gemini = None

    try:
        configuracion = types.GenerateContentConfig(response_mime_type="application/json")
        client = get_gemini_client()
        for modelo in MODELOS_CASCADA:
            try:
                print(f"[IA Gemini] (Opción 1) Procesando con {modelo}...")
                respuesta = client.models.generate_content(
                    model=modelo,
                    contents=prompt_completo,
                    config=configuracion
                )
                if respuesta and respuesta.text:
                    limpio = respuesta.text.strip()
                    if limpio.startswith("```"):
                        limpio = re.sub(r"^```(?:json)?\s*", "", limpio)
                        limpio = re.sub(r"\s*```$", "", limpio)
                    datos = json.loads(limpio)
                    datos["modelo_ia"] = f"gemini/{modelo}"
                    print(f"[IA Gemini] ¡Éxito con {modelo}!")
                    return datos
            except Exception as e_mod:
                ultimo_error_gemini = e_mod
                print(f"[IA Gemini] Error en modelo {modelo}: {e_mod}")
                continue
    except Exception as e_client:
        ultimo_error_gemini = e_client
        print(f"[IA Gemini] No se pudo inicializar cliente Gemini: {e_client}")

    # -------------------------------------------------------------
    # 2. INTENTAR CON GROQ (2ª OPCIÓN: Fallback si Gemini falla)
    # -------------------------------------------------------------
    groq_api_key = os.getenv("GROQ_API_KEY")
    ultimo_error_groq = None
    if groq_api_key:
        print(f"[IA Groq] Gemini no estuvo disponible ({ultimo_error_gemini}). Intentando con Groq (2ª opción)...")
        groq_models = [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b"
        ]
        
        messages = [
            {
                "role": "system",
                "content": f"Eres el tutor pedagógico inteligente de StudNova IA. Debes responder EXCLUSIVAMENTE con un objeto JSON válido siguiendo estas reglas:\n\n{PROMPT_TUTOR_PROFUNDO}\n\n{bloque_restricciones}"
            }
        ]
        for msg in historial:
            rol = "user" if msg.get("rol") == "usuario" else "assistant"
            messages.append({"role": rol, "content": msg.get("texto") or ""})
            
        prompt_groq_final = f"{prompt_usuario}\n\n{instruccion_accion}"
        if bloque_documento:
            prompt_groq_final += f"\n\n{bloque_documento}"
        messages.append({"role": "user", "content": prompt_groq_final})

        for modelo in groq_models:
            try:
                print(f"[IA Groq] (Opción 2) Procesando con {modelo}...")
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": modelo,
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                        "max_completion_tokens": 8192,
                        "temperature": 0.4
                    },
                    timeout=60
                )
                if resp.status_code == 200:
                    raw_content = resp.json()["choices"][0]["message"]["content"]
                    limpio = raw_content.strip()
                    if limpio.startswith("```"):
                        limpio = re.sub(r"^```(?:json)?\s*", "", limpio)
                        limpio = re.sub(r"\s*```$", "", limpio)
                    datos = json.loads(limpio)
                    datos["modelo_ia"] = f"groq/{modelo}"
                    print(f"[IA Groq] ¡Éxito con {modelo}!")
                    return datos
                else:
                    ultimo_error_groq = f"{resp.status_code} - {resp.text[:200]}"
                    print(f"[IA Groq] Error en {modelo}: {ultimo_error_groq}")
            except Exception as e_groq:
                ultimo_error_groq = e_groq
                print(f"[IA Groq] Excepción con {modelo}: {e_groq}")
                continue
    else:
        print("[IA Groq] GROQ_API_KEY no configurada para fallback.")

    # -------------------------------------------------------------
    # 3. MODO CONTINGENCIA SEGURO (Garantiza múltiples módulos)
    # -------------------------------------------------------------
    print(f"[IA Contingencia] Activando modo contingencia por error en proveedores (Gemini: {ultimo_error_gemini}, Groq: {ultimo_error_groq})")
    return generar_plan_contingencia(prompt_usuario)


def generar_plan_contingencia(prompt_usuario: str) -> dict:
    prompt_limpio = prompt_usuario.lower()
    materia = "Álgebra Lineal" if "algebra" in prompt_limpio else \
              "Física Cuántica" if "fisica" in prompt_limpio or "cuantica" in prompt_limpio else \
              "Programación en Python" if "python" in prompt_limpio else \
              "Cálculo Diferencial" if "calculo" in prompt_limpio else \
              "Ciencia de Datos" if "datos" in prompt_limpio else \
              prompt_usuario.replace("creame un plan de estudio sobre", "").replace("creame un plan de estudios sobre", "").replace("crea un plan sobre", "").replace("quiero aprender", "").strip().title() or "Aprendizaje Personalizado"

    palabras_plan = ["plan", "estudio", "curso", "ruta", "aprender", "modulo", "modulos", "semana", "semanas"]
    es_solicitud_plan = any(p in prompt_limpio for p in palabras_plan)

    if not es_solicitud_plan and len(prompt_usuario.split()) < 4:
        return {
            "tipo": "conversacion",
            "mensaje": f"¡Hola! 👋 Me encanta el tema **{materia}**. Para armar tu plan a medida, ¿en cuántas semanas planeas estudiarlo y en cuántos módulos te gustaría distribuirlo?"
        }

    return {
        "tipo": "plan_generado",
        "mensaje": f"✨ He generado tu plan de estudio sobre {materia}:",
        "plan": {
            "titulo": f"Dominio Integral de {materia}",
            "descripcion": f"Ruta pedagógica estructurada en módulos con lecciones profundas, ejemplos paso a paso y comprobación de conceptos para {materia}.",
            "materia": materia,
            "recomendacion_fatiga": "Estudia 25 minutos seguidos y realiza 5 minutos de pausa activa para consolidar la memoria.",
            "modulos": [
                {
                    "id": "mod-1",
                    "nivel_tag": "Nivel 1: Fundamentos Esenciales",
                    "nivel_clase": "basico",
                    "titulo": f"Fundamentos y Principios de {materia}",
                    "teoria_modulo": f"Marco teórico inicial que abarca las definiciones formales, axiomas y pilares conceptuales necesarios para abordar {materia}.",
                    "lecciones": [
                        {
                            "titulo": f"Introducción a los Conceptos Clave de {materia}",
                            "duracion_minutos": 45,
                            "concepto_teorico": f"El dominio de {materia} inicia comprendiendo sus definiciones fundamentales y su campo de acción. A través de este módulo se sientan las bases sólidas para avanzar hacia conceptos complejos con rigor y claridad.",
                            "puntos_clave": [
                                f"Definición y propiedades estructurales en {materia}.",
                                "Notación matemática y simbólica estándar.",
                                "Casos representativos de aplicación directa."
                            ],
                            "ejemplo_codigo_o_formula": "Demostración guiada del axioma principal y su interpretación geométrica o analítica.",
                            "ejercicio_practico": {
                                "enunciado": f"Aplica los conceptos iniciales de {materia} para resolver el caso base propuesto.",
                                "solucion_paso_a_paso": "Paso 1: Identificar las hipótesis del enunciado.\nPaso 2: Aplicar la definición formal.\nPaso 3: Verificar la validez del resultado."
                            }
                        }
                    ],
                    "mini_quizzes": [
                        {
                            "titulo": "Comprobación de Concepto",
                            "pregunta": f"¿Cuál es el propósito principal de los axiomas fundamentales en {materia}?",
                            "opciones": [
                                "Establecer las bases teóricas rigurosas y consistentes",
                                "Sustituir la demostración por suposiciones",
                                "Evitar el análisis formal",
                                "Reducir la precisión de los cálculos"
                            ],
                            "indice_correcto": 0,
                            "explicacion": "Los axiomas garantizan la consistencia y validez de todas las deducciones posteriores."
                        }
                    ]
                },
                {
                    "id": "mod-2",
                    "nivel_tag": "Nivel 2: Operaciones y Transformaciones",
                    "nivel_clase": "intermedio",
                    "titulo": f"Operaciones y Métodos en {materia}",
                    "teoria_modulo": f"Profundización en las operaciones estructuradas, técnicas de manipulación algebraica y métodos computacionales de {materia}.",
                    "lecciones": [
                        {
                            "titulo": "Técnicas de Transformación y Algoritmos",
                            "duracion_minutos": 50,
                            "concepto_teorico": "Aprenderás los procedimientos sistemáticos para descomponer sistemas y operar de manera óptima bajo diferentes condiciones.",
                            "puntos_clave": [
                                "Algoritmos estándar de resolución.",
                                "Invariantes y propiedades bajo transformación.",
                                "Errores comunes y cómo evitarlos."
                            ],
                            "ejemplo_codigo_o_formula": "Algoritmo de resolución paso a paso con validación cruzada.",
                            "ejercicio_practico": {
                                "enunciado": "Calcula la solución analítica del sistema propuesto.",
                                "solucion_paso_a_paso": "Paso 1: Construir la representación formal.\nPaso 2: Ejecutar las transformaciones elementales.\nPaso 3: Interpretar la solución resultante."
                            }
                        }
                    ],
                    "mini_quizzes": [
                        {
                            "titulo": "Comprobación de Concepto",
                            "pregunta": "¿Qué ventaja ofrece un método sistemático frente a un cálculo empírico?",
                            "opciones": [
                                "Garantiza reproducibilidad, convergencia y menor probabilidad de error",
                                "Aumenta la complejidad sin ningún beneficio",
                                "Elimina la necesidad de interpretar el resultado",
                                "Sólo funciona para un número finito de casos triviales"
                            ],
                            "indice_correcto": 0,
                            "explicacion": "Los métodos sistemáticos proporcionan garantías matemáticas sobre la validez de la solución."
                        }
                    ]
                },
                {
                    "id": "mod-3",
                    "nivel_tag": "Nivel 3: Aplicaciones Prácticas y Modelado",
                    "nivel_clase": "avanzado",
                    "titulo": f"Aplicaciones Prácticas y Modelado con {materia}",
                    "teoria_modulo": f"Aplicación del conocimiento adquirido para modelar problemas del mundo real en ciencias, ingeniería y computación.",
                    "lecciones": [
                        {
                            "titulo": "Modelado y Solución de Problemas del Mundo Real",
                            "duracion_minutos": 60,
                            "concepto_teorico": f"Se integran todos los conceptos para abordar escenarios prácticos donde {materia} es indispensable.",
                            "puntos_clave": [
                                "Traducción de un problema real a un modelo formal.",
                                "Optimización y análisis de sensibilidad.",
                                "Validación de conclusiones."
                            ],
                            "ejemplo_codigo_o_formula": "Caso práctico resuelto con aplicación integral de los módulos anteriores.",
                            "ejercicio_practico": {
                                "enunciado": "Modela el fenómeno descrito y determina la configuración óptima.",
                                "solucion_paso_a_paso": "Paso 1: Definir variables y restricciones.\nPaso 2: Resolver el modelo con las herramientas estudiadas.\nPaso 3: Presentar el informe de resultados."
                            }
                        }
                    ],
                    "mini_quizzes": [
                        {
                            "titulo": "Comprobación de Concepto",
                            "pregunta": "¿Por qué es crucial validar un modelo analítico frente a los datos reales?",
                            "opciones": [
                                "Para verificar que las hipótesis teóricas reflejan fielmente el comportamiento observado",
                                "Porque los modelos teóricos nunca fallan",
                                "Para descartar las observaciones experimentales",
                                "Para simplificar artificialmente el problema"
                            ],
                            "indice_correcto": 0,
                            "explicacion": "La validación empírica asegura que las conclusiones teóricas sean aplicables a la realidad."
                        }
                    ]
                }
            ]
        }
    }