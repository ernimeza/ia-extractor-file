import os, json, base64
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
import openai

# ── Credenciales ──────────────────────────────────────────────────────────────
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini-2024-07-18")  # modelo con visión habilitado

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Property Extractor (multi-image)")

class ExtractionResponse(BaseModel):
    operacion: str | None
    tipodepropiedad: str | None
    ciudades: List[str] | None
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
    amenidades: List[str] | None
    amoblado: str | None
    nombredeledificio: str | None
    piso: str | None
    estilo: str | None
    divisa: str | None
    ubicacion: str | None

# ── Endpoint ──────────────────────────────────────────────────────────────────
@app.post("/extract-image", response_model=ExtractionResponse)
async def extract_image(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "Se requiere al menos una imagen")

    # Convierte cada imagen en image_url Part
    image_parts = []
    for f in files:
        if not f.content_type or f.content_type.split("/")[0] != "image":
            raise HTTPException(400, f"{f.filename} no es una imagen válida")
        img_b64 = base64.b64encode(await f.read()).decode()
        image_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{f.content_type};base64,{img_b64}"
            }
        })

    # Mensajes
    system_msg = """
Eres un extractor de datos inmobiliarios experto. Analiza las siguientes imágenes
de fichas técnicas y devuelve SOLO un JSON con esta estructura EXACTA
(usa null donde falte data):
{ "operacion": ..., "tipodepropiedad": ..., ... }
"""
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": image_parts}
    ]

    # Llamada a OpenAI
    try:
        resp = openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        print("OpenAI error:", e)
        raise HTTPException(500, f"Error OpenAI: {e}")

    return json.loads(resp.choices[0].message.content)
