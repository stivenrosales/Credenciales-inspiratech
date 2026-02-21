#!/usr/bin/env python3
"""
Generador de Credenciales - Inspira Tech
Toma las fotos de estudiantes desde Airtable y las coloca dentro del
marco circular de la plantilla de credencial.
"""

import os
import sys
import time
import json
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageOps

# ── Configuracion ──────────────────────────────────────────────────
# La API key se lee de la variable de entorno AIRTABLE_API_KEY
# o del archivo .env en la misma carpeta del script
API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
if not API_KEY:
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith("AIRTABLE_API_KEY="):
                    API_KEY = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    if not API_KEY:
        print("ERROR: No se encontro AIRTABLE_API_KEY.")
        print("Opciones:")
        print("  1. Crear archivo .env con: AIRTABLE_API_KEY=tu_api_key")
        print("  2. Exportar variable: export AIRTABLE_API_KEY=tu_api_key")
        sys.exit(1)

BASE_ID = "appQSwwBh50GVi2k7"
TABLE_ID = "tblurzyOXLuB1aM6g"
PHOTO_FIELD_ID = "fldR9H5sFU81424Nc"       # Foto
CREDENTIAL_FIELD_ID = "fldOl2OHKtLVly2xz"  # Credencial (nuevo campo)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "(Lote 2).png")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "credenciales_output")

# Circulo interior de la plantilla (calculado por analisis de pixeles)
CIRCLE_CENTER_X = 551
CIRCLE_CENTER_Y = 537
CIRCLE_RADIUS = 364
CIRCLE_DIAMETER = CIRCLE_RADIUS * 2

AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def fetch_records(max_records=None):
    """Obtiene todos los registros de Airtable con paginacion."""
    records = []
    offset = None
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"

    while True:
        params = {
            "fields[]": ["ID student", PHOTO_FIELD_ID],
            "pageSize": 100,
        }
        if offset:
            params["offset"] = offset
        if max_records and not offset:
            params["maxRecords"] = max_records

        resp = requests.get(url, headers=AIRTABLE_HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()

        records.extend(data.get("records", []))
        offset = data.get("offset")

        if not offset or (max_records and len(records) >= max_records):
            break

    return records[:max_records] if max_records else records


def download_image(url):
    """Descarga una imagen desde URL y retorna un objeto PIL Image con orientacion EXIF corregida."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content))
    # Corregir orientacion segun metadatos EXIF (evita fotos volteadas/rotadas)
    img = ImageOps.exif_transpose(img)
    return img


def crop_and_resize_photo(photo, target_size):
    """
    Recorta la foto a un cuadrado (priorizando la parte superior para
    fotos verticales donde esta el rostro) y redimensiona al tamano objetivo.
    """
    w, h = photo.size

    if w == h:
        # Ya es cuadrado
        pass
    elif h > w:
        # Foto vertical: recortar cuadrado desde la parte superior
        # Tomamos un poco mas abajo del tope para capturar la cara
        top_offset = int(h * 0.05)  # 5% desde arriba
        box = (0, top_offset, w, top_offset + w)
        # Asegurarnos de no salir de los limites
        if box[3] > h:
            box = (0, h - w, w, h)
        photo = photo.crop(box)
    else:
        # Foto horizontal: recortar cuadrado centrado
        left = (w - h) // 2
        photo = photo.crop((left, 0, left + h, h))

    return photo.resize((target_size, target_size), Image.LANCZOS)


def create_circular_mask(size):
    """Crea una mascara circular."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask


def generate_credential(template, photo):
    """
    Genera una credencial colocando la foto dentro del circulo de la plantilla.
    """
    # Convertir template a RGBA para compositing
    credential = template.copy().convert("RGBA")

    # Preparar foto circular
    photo_resized = crop_and_resize_photo(photo, CIRCLE_DIAMETER)
    photo_rgba = photo_resized.convert("RGBA")

    # Crear mascara circular
    mask = create_circular_mask(CIRCLE_DIAMETER)

    # Posicion: esquina superior izquierda del bounding box del circulo
    paste_x = CIRCLE_CENTER_X - CIRCLE_RADIUS
    paste_y = CIRCLE_CENTER_Y - CIRCLE_RADIUS

    # Pegar la foto con mascara circular sobre la plantilla
    credential.paste(photo_rgba, (paste_x, paste_y), mask)

    # Convertir de vuelta a RGB para guardar como PNG sin canal alpha innecesario
    return credential.convert("RGB")


def upload_to_catbox(filepath):
    """Sube una imagen a litterbox.catbox.moe (hosting temporal 1h) y retorna la URL."""
    with open(filepath, "rb") as f:
        resp = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data={"reqtype": "fileupload", "time": "72h"},
            files={"fileToUpload": (os.path.basename(filepath), f, "image/png")},
            timeout=60,
        )
    resp.raise_for_status()
    url = resp.text.strip()
    if not url.startswith("http"):
        raise Exception(f"Upload fallo: {url}")
    return url


def update_airtable_credential(record_id, image_url, filename):
    """Actualiza el campo Credencial en Airtable con la URL de la imagen."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}/{record_id}"
    payload = {
        "fields": {
            CREDENTIAL_FIELD_ID: [{"url": image_url, "filename": filename}]
        }
    }
    resp = requests.patch(url, headers=AIRTABLE_HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def sanitize_filename(name):
    """Limpia un nombre para usarlo como nombre de archivo."""
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip()


def fetch_records_by_names(names_list):
    """Obtiene registros filtrados por una lista de nombres."""
    records = []
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"

    for name in names_list:
        # Buscar por nombre parcial con FIND
        search_name = name.strip()
        params = {
            "fields[]": ["ID student", PHOTO_FIELD_ID],
            "filterByFormula": f'FIND("{search_name}", {{ID student}})',
        }
        resp = requests.get(url, headers=AIRTABLE_HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()
        found = data.get("records", [])
        if found:
            records.append(found[0])
        else:
            print(f"  AVISO: No se encontro registro para '{search_name}'")

    return records


def main():
    # Determinar cuantos registros procesar
    max_records = None
    names_filter = None

    if len(sys.argv) > 1:
        if sys.argv[1] == "--names":
            # Modo filtro por nombres: leer lista del archivo o argumentos
            if len(sys.argv) > 2 and os.path.isfile(sys.argv[2]):
                with open(sys.argv[2]) as f:
                    names_filter = [line.strip() for line in f if line.strip()]
            else:
                names_filter = [" ".join(sys.argv[2:])]
            print(f"Modo filtro: procesando {len(names_filter)} nombre(s)")
        else:
            try:
                max_records = int(sys.argv[1])
                print(f"Modo prueba: procesando {max_records} registro(s)")
            except ValueError:
                pass

    # Crear directorio de salida
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Cargar plantilla
    print("Cargando plantilla...")
    template = Image.open(TEMPLATE_PATH)

    # Obtener registros de Airtable
    print("Obteniendo registros de Airtable...")
    if names_filter:
        records = fetch_records_by_names(names_filter)
    else:
        records = fetch_records(max_records)
    print(f"Total registros obtenidos: {len(records)}")

    success = 0
    errors = 0

    for i, record in enumerate(records, 1):
        record_id = record["id"]
        fields = record.get("fields", {})
        name = fields.get("ID student", f"sin_nombre_{record_id}")
        photos = fields.get("Foto", [])

        if not photos:
            print(f"  [{i}/{len(records)}] {name}: SIN FOTO - saltando")
            continue

        photo_url = photos[0]["url"]
        safe_name = sanitize_filename(name)

        print(f"  [{i}/{len(records)}] {name}...", end=" ", flush=True)

        try:
            # Descargar foto
            photo = download_image(photo_url)

            # Generar credencial
            credential = generate_credential(template, photo)

            # Guardar localmente
            output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.png")
            credential.save(output_path, "PNG", quality=95)

            # Subir a hosting temporal
            hosted_url = upload_to_catbox(output_path)

            # Actualizar Airtable
            update_airtable_credential(record_id, hosted_url, f"{safe_name}.png")

            print("OK")
            success += 1

        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

        # Pausa entre registros para no saturar APIs
        if i < len(records):
            time.sleep(0.5)

    print(f"\nResumen: {success} exitosos, {errors} errores de {len(records)} registros")


if __name__ == "__main__":
    main()
