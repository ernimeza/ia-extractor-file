import os, json, base64
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import openai, dotenv

# Cargar claves
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini-2024-07-18")  # modelo con visión habilitado

app = FastAPI(title="Property Extractor (10 images)")

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

def to_image_part(f: UploadFile) -> dict:
    if not f or not f.content_type or f.content_type.split("/")[0] != "image":
        raise HTTPException(400, f"{f.filename if f else 'Archivo'} no es una imagen válida")
    b64 = base64.b64encode(f.file.read()).decode()
    return {
        "type": "image_url",
        "image_url": { "url": f"data:{f.content_type};base64,{b64}" }
    }

@app.post("/extract-image", response_model=ExtractionResponse)
async def extract_image(
    img1: UploadFile = File(None), img2: UploadFile = File(None), img3: UploadFile = File(None),
    img4: UploadFile = File(None), img5: UploadFile = File(None), img6: UploadFile = File(None),
    img7: UploadFile = File(None), img8: UploadFile = File(None), img9: UploadFile = File(None),
    img10: UploadFile = File(None),
):
    imgs = [i for i in (img1, img2, img3, img4, img5, img6, img7, img8, img9, img10) if i]
    if not imgs:
        raise HTTPException(400, "Envía al menos una imagen (img1…)")

    image_parts = [to_image_part(f) for f in imgs]

    system_msg = """
Eres un extractor de datos inmobiliarios experto. Analiza estas imágenes de ficha técnica
y devuelve SOLO un JSON con la estructura indicada (usa null donde falte info).
"""
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": image_parts},
    ]

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
