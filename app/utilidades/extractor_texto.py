# app/utilidades/extractor_texto.py
import io
import os
import re
from pathlib import Path
from typing import Optional

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import pymupdf
except ImportError:
    pymupdf = None

try:
    from PIL import Image
    import pytesseract

    # Si Tesseract está instalado en la ruta por defecto de Windows, configurarlo automáticamente
    posibles_rutas_tesseract = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
    ]
    for ruta in posibles_rutas_tesseract:
        if os.path.exists(ruta):
            pytesseract.pytesseract.tesseract_cmd = ruta
            break
except ImportError:
    Image = None
    pytesseract = None


def limpiar_y_truncar_texto(texto: str, max_palabras: int = 12000) -> str:
    """
    Limpia espacios en blanco repetitivos, caracteres extraños
    y trunca el texto al número máximo de palabras para proteger la ventana de tokens.
    """
    if not texto:
        return ""

    # Normalizar saltos de línea y espacios
    texto = re.sub(r'\r\n', '\n', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    texto = texto.strip()

    palabras = texto.split()
    if len(palabras) > max_palabras:
        texto = " ".join(palabras[:max_palabras]) + "\n\n[...Texto resumido para optimización pedagógica y consumo de tokens...]"

    return texto


def extraer_texto_con_ocr(imagen_pil) -> str:
    """
    Ejecuta OCR sobre una imagen usando pytesseract.
    Maneja excepciones de forma segura si el binario no está instalado.
    """
    if not pytesseract or not Image:
        return ""
    try:
        # Intentar con español e inglés, si falla usar el idioma por defecto
        try:
            return pytesseract.image_to_string(imagen_pil, lang="spa+eng")
        except Exception:
            return pytesseract.image_to_string(imagen_pil)
    except Exception as e:
        print(f"[OCR] Aviso: No se pudo ejecutar OCR en imagen ({e})")
        return ""


def convertir_pdf_a_txt(contenido_bytes: bytes, nombre_archivo: str = "documento.pdf") -> str:
    """
    Convierte un PDF a texto plano (.txt).
    1. Intenta extracción directa de texto digital (ultrarrápida y sin pérdida).
    2. Si las páginas no tienen texto (son imágenes o documentos escaneados),
       renderiza las páginas a imagen y aplica OCR con pytesseract.
    """
    paginas_texto = []
    stream_pdf = io.BytesIO(contenido_bytes)

    # Paso 1: Intento primario con pypdf
    total_paginas = 0
    if PdfReader:
        try:
            lector = PdfReader(stream_pdf)
            total_paginas = len(lector.pages)
            for idx, pagina in enumerate(lector.pages):
                txt_pag = (pagina.extract_text() or "").strip()
                if txt_pag:
                    paginas_texto.append(f"--- Página {idx + 1} ---\n{txt_pag}")
                else:
                    # Página vacía de texto digital, podría ser escaneo
                    paginas_texto.append("")
        except Exception as e:
            print(f"[Extractor PDF] Aviso con pypdf en {nombre_archivo}: {e}")

    # Paso 2: Evaluar si el PDF requiere OCR (páginas vacías o escaneadas)
    texto_acumulado = " ".join(paginas_texto).strip()
    necesita_ocr = len(texto_acumulado) < 50 and pymupdf is not None

    if necesita_ocr:
        print(f"[Extractor PDF] Detectado PDF con poco o ningún texto digital ({len(texto_acumulado)} chars). Ejecutando OCR en {nombre_archivo}...")
        try:
            doc_pymupdf = pymupdf.open(stream=contenido_bytes, filetype="pdf")
            paginas_ocr = []
            for i, pagina in enumerate(doc_pymupdf):
                # Extraer texto digital con PyMuPDF primero
                txt = pagina.get_text().strip()
                if len(txt) > 30:
                    paginas_ocr.append(f"--- Página {i + 1} ---\n{txt}")
                    continue

                # Si es escaneo/imagen, renderizar a imagen y pasar OCR
                pix = pagina.get_pixmap(dpi=150)
                img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                txt_ocr = extraer_texto_con_ocr(img_pil).strip()
                if txt_ocr:
                    paginas_ocr.append(f"--- Página {i + 1} (OCR) ---\n{txt_ocr}")

            doc_pymupdf.close()
            if paginas_ocr:
                paginas_texto = paginas_ocr
        except Exception as e_pdf:
            print(f"[Extractor PDF] Error al procesar OCR con PyMuPDF: {e_pdf}")

    resultado_final = "\n\n".join([p for p in paginas_texto if p.strip()])
    return limpiar_y_truncar_texto(resultado_final)


def extraer_texto_de_archivo(contenido_bytes: bytes, nombre_archivo: str) -> str:
    """
    Punto de entrada principal para extraer texto de cualquier archivo admitido:
    - .pdf: Extracción nativa y OCR si es escaneo.
    - .txt / .md / .csv: Decodificación de texto.
    - .png / .jpg / .jpeg: OCR directo sobre la imagen.
    """
    ext = Path(nombre_archivo).suffix.lower()

    if ext == ".pdf":
        return convertir_pdf_a_txt(contenido_bytes, nombre_archivo)

    elif ext in [".txt", ".md", ".csv"]:
        # Intentar varias codificaciones comunes
        for codificacion in ["utf-8", "latin-1", "cp1252"]:
            try:
                texto = contenido_bytes.decode(codificacion)
                return limpiar_y_truncar_texto(texto)
            except UnicodeDecodeError:
                continue
        return limpiar_y_truncar_texto(contenido_bytes.decode("utf-8", errors="ignore"))

    elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
        if Image:
            try:
                img_pil = Image.open(io.BytesIO(contenido_bytes))
                texto_ocr = extraer_texto_con_ocr(img_pil)
                return limpiar_y_truncar_texto(texto_ocr)
            except Exception as e_img:
                print(f"[Extractor Imagen] Error al procesar imagen: {e_img}")
                return ""

    return ""
