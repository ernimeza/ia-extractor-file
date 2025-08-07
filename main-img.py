import os, json, base64
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini-2024-07-18")

app = FastAPI()

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

@app.post("/extract-image", response_model=ExtractionResponse)
async def extract_image(file: UploadFile = File(...)):
    if file.content_type.split("/")[0] != "image":
        raise HTTPException(400, "Solo se aceptan imágenes")
    img_b64 = base64.b64encode(await file.read()).decode()
    system = "Eres un extractor… (instruc. JSON exacto)"
    user   = f"<base64>\n{img_b64}\n</base64>"

    resp = await openai.chat.completions.create(
        model=MODEL,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":user}],
        temperature=0,
        max_tokens=1500,
        response_format={"type":"json_object"},
    )
    return json.loads(resp.choices[0].message.content)
