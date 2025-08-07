import os, json, base64, io
from fastapi import FastAPI, UploadFile, File, Body
from pydantic import BaseModel
import openai
from pdf2image import convert_from_bytes

openai.api_key = os.environ["OPENAI_API_KEY"]
MODEL = "gpt-4o-mini-2024-07-18"
app = FastAPI()

SYSTEM_PROMPT = """
Eres un extractor de datos inmobiliarios experto. Analiza el contenido proporcionado para extraer/inferir info. Devuelve SOLO un objeto JSON con esta estructura EXACTA (sin campos extras, usa null si no hay data). Corrige ortografía/capitalización para coincidir con listas.
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
  "hectareas": Hectáreas (integer),
  "m2t": Número de m² del terreno (integer),
  "m2c": Número de m² de construcción (integer),
  "estado": Elige exclusivamente de las siguientes opciones, si no hay información seleeciona la que mas se asemeje: ['A estrenar', 'Perfecto', 'Muy bueno', 'Bueno'] (string),
  "amenidades": Elige las opciones entre: ['Acceso controlado', 'Área de coworking', 'Área de parrilla', 'Área de yoga', 'Área verde', 'Bar', 'Bodega', 'Cancha de pádel', 'Cancha de tenis', 'Cancha de fútbol', 'Cerradura digital', 'Cine', 'Club house', 'Estacionamiento techado', 'Generador', 'Gimnasio', 'Laguna artificial', 'Laguna natural', 'Lavandería', 'Parque infantil', 'piscina', 'Quincho', 'Salón de eventos', 'Sala de juegos', 'Sala de masajes', 'Sala de reuniones', 'Sauna', 'Seguridad 24/7', 'Solarium', 'Spa', 'Terraza', 'Wi-Fi', 'Café', 'Business center'] (list),
  "amoblado": Elige de: ['Sí', 'No'] (string),
  "descripcion": Linda descripción de la propiedad, bien estructurada, dejando una linea al concluir el parrafo yendo al grano, con emojies y checklist con beneficios si hay contenido (string),
  "nombredeledificio": Nombre del edificio (string),
  "piso": Piso en el que se encuentra (string),
  "estilo": Elige de: ['Moderna', 'Minimalista', 'Clásica', 'De campo'] (string),
  "divisa": Elige de: ['GS', '$'] (string),
  "ubicacion": Dirección completa formateada como en Google Maps (string)
}
"""

class TextReq(BaseModel):
    description: str

@app.post("/extract-text")
async def extract_text(req: TextReq = Body(...)):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [{"type": "text", "text": req.description}]}
    ]
    resp = openai.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )
    print("JSON de respuesta desde OpenAI:", resp.choices[0].message.content)
    return json.loads(resp.choices[0].message.content)

@app.post("/extract-file")
async def extract_file(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename.lower()
    base64_images = []
    if filename.endswith('.pdf'):
        images = convert_from_bytes(content)
        for img in images:
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            base64_images.append(base64_str)
    else:
        base64_str = base64.b64encode(content).decode('utf-8')
        base64_images.append(base64_str)
    user_content = [
        {"type": "text", "text": "Extrae los datos inmobiliarios de esta imagen o documento (ficha técnica)."}
    ] + [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "low"}}
        for b64 in base64_images
    ]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
    resp = openai.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )
    print("JSON de respuesta desde OpenAI:", resp.choices[0].message.content)
    return json.loads(resp.choices[0].message.content)
