import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent


def limpiar_bloques_markdown(texto: str) -> str:
    """Extrae el contenido dentro de ```html ... ``` si la IA lo envuelve en markdown."""
    match = re.search(r"```(?:html|xml)?\s*(.*?)\s*```", texto, re.DOTALL)
    if match:
        return match.group(1).strip()
    return texto.strip()


def procesar_y_guardar_codigo(codigo_ia_crudo, destino_carpeta="ia", nombre_base="generado_ia"):
    """
    Parsea el HTML de Gemini, extrae TODO el CSS y JS usando get_text(),
    y los guarda en archivos independientes en la carpeta 'ia/'.
    """
    # 1. Limpiar posibles bloques markdown
    codigo_limpio = limpiar_bloques_markdown(codigo_ia_crudo)
    
    # 2. Parsear con BeautifulSoup
    soup = BeautifulSoup(codigo_limpio, 'html.parser')
    
    # ---------------------------------------------------------
    # 3. EXTRAER CSS (usamos get_text() para no perder nada)
    # ---------------------------------------------------------
    estilos = []
    for tag_style in soup.find_all('style'):
        texto_css = tag_style.get_text()  # <-- get_text() captura todo el contenido real
        if texto_css:
            estilos.append(texto_css.strip())
        tag_style.decompose()  # Elimina el tag <style> del HTML
    
    css_final = "\n\n".join(estilos)
    
    # ---------------------------------------------------------
    # 4. EXTRAER JAVASCRIPT (usamos get_text() para no perder lógica con '<' o '>')
    # ---------------------------------------------------------
    scripts = []
    for tag_script in soup.find_all('script'):
        # Solo scripts internos (ignoramos librerías externas con src="...")
        if not tag_script.get('src'):
            texto_js = tag_script.get_text()
            if texto_js:
                scripts.append(texto_js.strip())
            tag_script.decompose()  # Elimina el tag <script> del HTML
            
    js_final = "\n\n".join(scripts)
    
    # ---------------------------------------------------------
    # 5. EXTRAER CONTENIDO HTML
    # ---------------------------------------------------------
    if soup.body:
        html_contenido = soup.body.decode_contents()
    else:
        html_contenido = str(soup)
        
    # ---------------------------------------------------------
    # 6. GUARDAR ARCHIVOS EN EL DISCO
    # ---------------------------------------------------------
    carpeta_destino = ROOT_DIR / destino_carpeta
    carpeta_destino.mkdir(parents=True, exist_ok=True)
    
    ruta_html = carpeta_destino / f"{nombre_base}.html"
    ruta_css  = carpeta_destino / f"{nombre_base}.css"
    ruta_js   = carpeta_destino / f"{nombre_base}.js"
    
    # Guardar CSS
    with open(ruta_css, "w", encoding="utf-8") as f:
        f.write(css_final)
        
    # Guardar JS
    with open(ruta_js, "w", encoding="utf-8") as f:
        f.write(js_final)
        
    # Plantilla HTML con rutas absolutas /ia/... para que siempre carguen
    plantilla_final = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StudNova IA - Plan de Estudio</title>
    <!-- Vinculación del CSS generado -->
    <link rel="stylesheet" href="/ia/{nombre_base}.css">
</head>
<body>

{html_contenido.strip()}

    <!-- Vinculación del JS generado -->
    <script src="/ia/{nombre_base}.js"></script>
</body>
</html>"""

    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(plantilla_final)
        
    return {
        "html": html_contenido.strip(),
        "css": css_final,
        "js": js_final,
        "rutas": {
            "html": str(ruta_html),
            "css": str(ruta_css),
            "js": str(ruta_js)
        }
    }