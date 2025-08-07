import os, json, base64
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import openai, dotenv

# ── Credenciales ──────────────────────────────────────────────────────────────
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini-2024-07-18")  # cambia si usas otro modelo con visión

# ── Instancia FastAPI ─────────────────────────────────────────────────────────
app = FastAPI(title="Property Extractor (10 images)")

# ── Función auxiliar para convertir archivo → image_url part ──────────────────
def to_image_part(f: UploadFile) -> dict:
    if not f or not f.content_type or f.content_type.split("/")[0] != "image":
        raise HTTPException(400, f"{f.filename if f else 'Archivo'} no es una imagen válida")
    b64 = base64.b64encode(f.file.read()).decode()
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{f.content_type};base64,{b64}"}
    }

# ── Endpoint ──────────────────────────────────────────────────────────────────
@app.post("/extract-image")
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

    # ── Prompt con TODOS los campos que quieres ───────────────────────────────
    system_msg = """
Eres un extractor de datos inmobiliarios experto. Analiza las imágenes de ficha técnica
y devuelve SOLO un objeto JSON con esta estructura EXACTA (sin campos extra, usa null si no hay dato):

{
  "operacion": "venta" | "alquiler",
  "tipodepropiedad": "casas" | "departamentos" | "duplex" | "terrenos" | "oficinas" | "locales" | "edificios" | "paseos" | "depositos" | "quintas" | "estancias",
  "ciudades": "<una de la lista larga proporcionada>",
  "barrioasu": "<uno de la lista de barrios>",
  "precio": <número USD>,
  "habitaciones": "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "monoambiente" | "+10",
  "banos": "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "+10",
  "cocheras": "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "+10",
  "plantas": "1" | "2" | "3" | "4" | "5" | "+5",
  "m2": <entero>,
  "anno_construccion": <entero>,
  "hectareas": <entero>,
  "m2t": <entero>,  // m² del terreno
  "m2c": <entero>,  // m² de construcción
  "estado": "A estrenar" | "Perfecto" | "Muy bueno" | "Bueno",
  "amenidades": ["Acceso controlado", "Área de coworking", ...]  // máximo coincide con tu lista
  "amoblado": "Sí" | "No",
  "descripcion": "<texto atractivo con emojis y checklist>",
  "nombredeledificio": "<string>",
  "piso": "<string>",
  "estilo": "Moderna" | "Minimalista" | "Clásica" | "De campo",
  "divisa": "GS" | "$",
  "ubicacion": "<dirección completa Google Maps>"
}
"""

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": image_parts},
    ]

    # ── Llamada a OpenAI ───────────────────────────────────────────────────────
    try:
        resp = openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0,
            max_tokens=1800,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        print("OpenAI error:", e)
        raise HTTPException(500, f"Error OpenAI: {e}")

    # ── Devolver JSON sin validar ─────────────────────────────────────────────
    return JSONResponse(content=json.loads(resp.choices[0].message.content))
