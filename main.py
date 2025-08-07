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
y devuelve SOLO un objeto JSON con esta estructura EXACTA (sin campos extra).
**Si no puedes inferir un dato, escribe null (no inventes valores).**:

{
  "operacion": Elige de: ['venta', 'alquiler'] (string),
  "tipodepropiedad": Elige exactamente de: ['casas', 'departamentos', 'duplex', 'terrenos', 'oficinas', 'locales', 'edificios', 'paseos', 'depositos', 'quintas', 'estancias'] (string),
  "ciudades": Elige de: ['asuncion', 'luque', 'ciudad-del-este', 'encarnacion', 'san-lorenzo', 'fernando-de-la-mora', 'mariano-roque-alonso', 'san-bernardino', 'lambare', 'capiata', 'nemby', 'abai', 'acahay', 'alberdi', 'alborada', 'alto-vera', 'altos', 'antequera', 'aregua', 'arroyos-y-esteros', 'atyra', 'azotey', 'bella-vista-amambay', 'bahia-negra', 'bella-vista-Itapua', 'belen', 'benjamin-aceval', 'borja', 'buena-vista', 'caacupe', 'caaguazu', 'caballero', 'caapucu', 'caazapa', 'capiibary', 'capitan-bado', 'capitan-meza', 'caraguatay', 'capitan-miranda', 'carapegua', 'carlos-antonio-lopez', 'carayao', 'carmelo-peralta', 'capiibary', 'cerrito', 'chore', 'colonia-independencia', 'coronel-bogado', 'concepcion', 'coronel-martinez', 'coronel-oviedo', 'corpus-christi', 'curuguaty', 'desmochados', 'doctor-cecilio-baez-guaira', 'doctor-bottrell', 'doctor-cecilio-baez-caaguazu', 'doctor-j-victor-barrios', 'doctor-moises-bertoni', 'domingo-martinez-de-irala', 'edelira', 'emboscada', 'escobar', 'esteban-martinez', 'eugenio-a-garay', 'eusebio-ayala', 'filadelfia', 'felix-perez-cardozo', 'fuerte-olimpo', 'fram', 'francisco-caballero-alvarez', 'general-artigas', 'general-delgado', 'general-diaz', 'general-elizardo-aquino', 'general-iginio-morinigo', 'guayaibi', 'guarambare', 'guazu-cua', 'hernandarias', 'hohenau', 'humaitá', 'horqueta', 'independencia', 'isla-pucu', 'Ita', 'isla-umbu', 'itacurubi-de-la-cordillera', 'itacurubi-del-rosario', 'itape', 'itaugua', 'iturbe', 'iruna', 'jesus-de-tavarangue', 'jose-augusto-saldivar', 'jose-domingo-ocampos', 'jose-fasardi', 'jose-falcon', 'juan-de-mena', 'juan-manuel-frutos-pastoreo', 'juan-eulogio-estigarribia-campo-9', 'juan-leon-mallorquin', 'juan-emilio-oleary', 'la-colmena', 'karapai', 'katuete', 'la-paloma', 'la-pastora', 'la-victoria', 'laureles', 'leandro-oviedo', 'lima', 'limpio', 'loma-grande', 'loma-plata', 'los-cedrales', 'loreto', 'mbaracayu', 'mbocayaty-del-yhaguy', 'mbocayaty', 'mbocayaty-del-guaira', 'maracana', 'mariscal-estigarribia', 'mariscal-francisco-solano-lopez', 'mayor-julio-d-otano', 'mayor-jose-dejesus-martinez', 'mbocayaty', 'minga-guazu', 'natalicio-talavera', 'nanawa', 'naranjal', 'nueva-alborada', 'natalio', 'nueva-asuncion', 'nueva-colombia', 'nueva-italia', 'nueva-germania', 'nueva-toledo', 'nacunday', 'numi', 'olbligado', 'paso-barreto', 'paso-de-patria', 'paso-yobai', 'pedro-juan-caballero', 'pirapo', 'pirayu', 'pilar', 'piribebuy', 'pozo-colorado', 'presidente-franco', 'primero-de-marzo', 'puerto-adela', 'puerto-casado', 'puerto-irala', 'puerto-pinasco', 'quyquyho', 'raul-arsenio-oviedo', 'repatriacion', 'R-I-3-corrales', 'san-alberto', 'salto-del-guaira', 'san-antonio', 'san-carlos-del-apa', 'san-cosme-y-damian', 'san-estanislao-santani', 'san-joaquin', 'san-jose-obrero', 'san-juan-bautista-de-las-misiones', 'san-juan-bautista-de-neembucu', 'san-juan-del-parana', 'san-lazaro', 'san-miguel', 'san-pedro-del-parana', 'san-patricio', 'san-pablo', 'san-roque-gonzalez-de-santa-cruz', 'san-pedro-de-ycuamandyyu', 'san-salvador', 'san-vicente-pancholo', 'santa-elena', 'santa-maria', 'santa-fe-del-parana', 'santa-rosa', 'santa-maria-de-fe', 'santa-rosa-de-lima', 'santa-rosa-del-aguaray', 'santa-rosa-del-mbutuy', 'santa-rosa-del-monday', 'santiago', 'sapucai', 'sergeant-jose-felix-lopez-puentesino', 'simon-bolivar', 'tacuaras', 'tacuati', 'tavai', 'tavapy', 'tebicuary-mi', 'tembiaporã', 'teniente-esteban-martinez', 'tinfunque', 'tomas-romero-pereira', 'tobati', 'tres-de-mayo', 'trinidad', 'union', 'valenzuela', 'vaqueria', 'villa-del-rosario', 'villa-florida', 'villa-elisa', 'villa-franca', 'villa-hayes', 'villa-oliva', 'villa-rica', 'villeta', 'yabebyry', 'yaguaron', 'yasy-cany', 'yataity', 'yataity-del-Norte', 'ybycui', 'yby-pyta', 'yby-yau', 'ybyrarobana', 'yguazu', 'yhu', 'ypacarai', 'ypane', 'yuty', 'zanja-pyta'] (string),
  "barrioasu": Elige de: ['villa-morra', 'recoleta', 'carmelitas', 'las-lomas', 'las-mercedes', 'mburucuya', 'jara', 'sajonia', 'villa-aurelia', 'ycua-sati', 'banco-san-miguel', 'bañado-cara-cara', 'bernardino-caballero', 'obrero', 'bella-vista', 'Botanico', 'cañada-del-ybyray', 'carlos-a-lopez', 'catedral', 'ciudad-nueva', 'dr-francia', 'la-encarnación', 'general-diaz', 'herrera', 'hipodromo', 'ita-enramada', 'ita-pyta-punta', 'jukyty', 'los-laureles', 'loma-pyta', 'madame-lynch', 'manora', 'mcal-estigarribia', 'mcal-lopez', 'mbocayaty', 'mburicao', 'nazareth', 'ñu-guazu', 'panambi-reta', 'panambi-vera', 'pettirossi', 'pinoza', 'pirizal', 'republicano', 'chacarita', 'roberto-l-pettit', 'salvador-del-mundo', 'san-antonio', 'san-blas', 'san-cayetano', 'san-cristobal', 'san-jorge', 'san-juan', 'san-pablo', 'san-roque', 'san-vicente', 'santa-ana', 'santa-librada', 'santa-maria', 'santa-rosa', 'santisima-trinidad', 'santo-domingo', 'silvio-pettirossi', 'tablada-nueva', 'tacumbu', 'tembetary', 'terminal', 'virgen-de-fatima', 'virgen-de-la-asuncion', 'virgen-del-huerto', 'vista-alegre', 'ytay', 'zeballos-cue'] (string),
  "precio": Número en USD (integer),
  "habitaciones": Elige de: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'monoambiente', '+10'] (string),
  "banos": Elige de: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '+10'] (string),
  "cocheras": Elige de: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '+10'] (string),
  "plantas": Elige de: ['1', '2', '3', '4', '5', '+5'] (string),
  "m2": Número de m² (integer),
  "anno_construccion": Año de construcción (integer),
  "hectareas": Hectáreas (integer)
  "m2t": Número de m² del terreno (integer)
  "m2c": Número de m² de construcción, (integer)
  "estado": Elige exclusivamente de las siguientes opciones, si no hay información seleeciona la que mas se asemeje: ['A estrenar', 'Perfecto', 'Muy bueno', 'Bueno'] (string),
  "amenidades": Elige las opciones entre: ['Acceso controlado', 'Área de coworking', 'Área de parrilla', 'Área de yoga', 'Área verde', 'Bar', 'Bodega', 'Cancha de pádel', 'Cancha de tenis', 'Cancha de fútbol', 'Cerradura digital', 'Cine', 'Club house', 'Estacionamiento techado', 'Generador', 'Gimnasio', 'Laguna artificial', 'Laguna natural', 'Lavandería', 'Parque infantil', 'piscina', 'Quincho', 'Salón de eventos', 'Sala de juegos', 'Sala de masajes', 'Sala de reuniones', 'Sauna', 'Seguridad 24/7', 'Solarium', 'Spa', 'Terraza', 'Wi-Fi', 'Café', 'Business center'] (list),
  "amoblado": Elige de: ['Sí', 'No'] (string)
  "descripcion": Linda descripción de la propiedad, bien estructurada, dejando una linea al concluiir el parrafo yendo al grano, con emojies y checklist con beneficios si hay contenido (string),
  "nombredeledificio": Nombre del edificio (string),
  "piso": Piso en el que se encuentra (string),
  "estilo": Elige de: ['Moderna', 'Minimalista', 'Clásica', 'De campo'] (string),
  "divisa": Elige de: ['GS', '$'] (string),
  "ubicacion": Dirección completa formateada como en Google Maps (string)
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

    # ── Registrar y devolver JSON ─────────────────────────────────────────────
    result_json = json.loads(resp.choices[0].message.content)  # ← dict
    print("OpenAI result:", result_json)                       # ← logs Railway
    return JSONResponse(content=result_json)
