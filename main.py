import os
import json
import base64
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import openai

# ── Carga de credenciales ─────────────────────────────────────────────────────
load_dotenv()                                       # Lee .env en local; ignora en Railway
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-vision-preview") # Asegúrate de usar un modelo con visión

# ── Instancia FastAPI ─────────────────────────────────────────────────────────
app = FastAPI(title="Property Extractor (image)")

# ── Esquema de respuesta ──────────────────────────────────────────────────────
class ExtractionResponse(BaseModel):
    operacion: str | None
    tipodepropiedad: str | None
    ciudades: list[str] | None
    barrioasu: str | None
    precio: int | None
    habitaciones: str | None
    banos: str | None
    cocheras: str | None
    plantas: str | None
    m2: int | None
    anno_construccion: int | None
    hectareas: int | None
    m2t: int | None
    estado: str | None
    amenidades: list[str] | None
    amoblado: str | None
    nombredeledificio: str | None
    piso: str | None
    estilo: str | None
    divisa: str | None
    ubicacion: str | None

# ── Endpoint principal ────────────────────────────────────────────────────────
@app.post("/extract-image", response_model=ExtractionResponse)
async def extract_image(file: UploadFile = File(...)):
    # 1) Validar tipo de archivo
    if not file.content_type or file.content_type.split("/")[0] != "image":
        raise HTTPException(400, "Solo se aceptan imágenes")
    
    # 2) Leer y codificar
    img_bytes = await file.read()
    img_b64   = base64.b64encode(img_bytes).decode()
    mime      = file.content_type           # ej. image/png
    
    # 3) Construir mensajes para OpenAI
    system_msg = """
Eres un extractor de datos inmobiliarios experto. Analiza la imagen de la ficha técnica
y devuelve SOLO un JSON con esta estructura EXACTA (usa null donde falte info):
{
  "operacion": ...,
  "tipodepropiedad": ...,
  "ciudades": [...],
  "barrioasu": ...,
  "precio": ...,
  "habitaciones": ...,
  "banos": ...,
  "cocheras": ...,
  "plantas": ...,
  "m2": ...,
  "anno_construccion": ...,
  "hectareas": ...,
  "m2t": ...,
  "estado": ...,
  "amenidades": [...],
  "amoblado": ...,
  "nombredeledificio": ...,
  "piso": ...,
  "estilo": ...,
  "divisa": ...,
  "ubicacion": ...
}
"""
    image_part = {
        "type": "image_url",
        "image_url": {
            "url": f"data:{mime};base64,{img_b64}"
        }
    }

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": [image_part]}
    ]

    # 4) Llamar a OpenAI
    try:
        resp = await openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        # Se loguea en Railway y se propaga el error al cliente
        print("OpenAI error:", e)
        raise HTTPException(500, f"Error OpenAI: {e}")

    # 5) Devolver JSON
    return json.loads(resp.choices[0].message.content)
