import os
import uuid
import qrcode
from PIL import Image, ImageOps
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from ai_engine import process_guelaguetza_ai

app = FastAPI(
    title="Kiosco Guelaguetza IA API",
    description="Backend en Python + FastAPI con Generador de QR Propio",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def read_root():
    return {"status": "online", "message": "API Guelaguetza IA y QR Propio Lista 🚀"}


@app.post("/api/generate_image")
async def generate_image(image: UploadFile = File(...)):
    try:
        session_id = uuid.uuid4().hex[:8]
        orig_filename = f"original_{session_id}.jpg"
        ai_filename = f"guelaguetza_{session_id}.jpg"

        orig_path = os.path.join(UPLOAD_DIR, orig_filename)
        ai_path = os.path.join(UPLOAD_DIR, ai_filename)

        # 1. Guardar foto original
        with open(orig_path, "wb") as buffer:
            buffer.write(await image.read())

        # 2. Aplicar el motor de IA de estudio fotográfico
        process_guelaguetza_ai(orig_path, ai_path)

        return {
            "success": True,
            "message": "Imagen procesada con éxito",
            "original_image": f"uploads/{orig_filename}",
            "ai_image": f"uploads/{ai_filename}"
        }

    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/register_session")
async def register_session(
    ai_image: str = Form("uploads/default.jpg")
):
    try:
        session_id = uuid.uuid4().hex[:8]
        download_code = session_id.upper()
        
        base_server_url = "http://localhost:8000"
        
        # Limpiar la ruta por si viene con slashes invertidos o parámetros
        ai_filename = os.path.basename(ai_image.split("?")[0])
        download_url = f"{base_server_url}/uploads/{ai_filename}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(download_url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_framed = ImageOps.expand(qr_img, border=15, fill="white")

        qr_filename = f"qr_{session_id}.png"
        qr_path = os.path.join(UPLOAD_DIR, qr_filename)
        qr_framed.save(qr_path, "PNG")

        return {
            "success": True,
            "message": "QR generado correctamente",
            "session_id": session_id,
            "code": download_code,
            "url": download_url,
            "qr": f"uploads/{qr_filename}"
        }

    except Exception as e:
        print(f"❌ Error en register_session: {e}")
        return {"success": False, "message": str(e)}