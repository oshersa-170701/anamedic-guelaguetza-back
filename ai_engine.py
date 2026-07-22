import os
import cv2
import numpy as np
import random
from PIL import Image, ImageEnhance
from rembg import remove

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def process_guelaguetza_ai(input_path: str, output_path: str) -> bool:
    try:
        if not os.path.exists(input_path):
            print(f"❌ No existe imagen de entrada: {input_path}")
            return False

        # 1. Cargar la imagen de la cámara
        input_image = Image.open(input_path).convert("RGB")

        print("🤖 Procesando con IA (rembg): Limpiando fondo...")
        # 2. Quitar fondo con rembg
        transparent_person_img = remove(input_image)

        # 🌟 RETOQUE FOTOGRÁFICO DE ESTUDIO
        enhancer_contrast = ImageEnhance.Contrast(transparent_person_img)
        transparent_person_img = enhancer_contrast.enhance(1.10)

        enhancer_color = ImageEnhance.Color(transparent_person_img)
        transparent_person_img = enhancer_color.enhance(1.12)

        # 3. Seleccionar fondo turístico de Oaxaca al azar (incluyendo el marco especial)
        backgrounds = [
            "montealban.png",
            "tule.png",
            "centrohistorico.png",
            "guelaguetza (2).png", # 🌟 Marco con elementos superiores y letras
            "santodomingo.png",
            "mitla.png"
        ]
        
        valid_bgs = [bg for bg in backgrounds if os.path.exists(os.path.join(ASSETS_DIR, bg))]
        if not valid_bgs:
            valid_bgs = ["montealban.png"]

        chosen_bg = random.choice(valid_bgs)
        bg_path = os.path.join(ASSETS_DIR, chosen_bg)

        print(f"🎨 Fusionando persona con el fondo turístico: {chosen_bg}")
        
        # 4. Cargar fondo turístico en HD (1280x720)
        bg_img = Image.open(bg_path).convert("RGBA")
        target_width = 1280
        target_height = 720
        bg_img = bg_img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # 🌟 DETECCIÓN DE MARCO: Si se eligió el marco de Guelaguetza con centro negro, 
        # lo separamos como capa superior (overlay) y usamos un fondo limpio base.
        frame_overlay = None
        if "guelaguetza (2)" in chosen_bg.lower() or "guelaguetza" in chosen_bg.lower():
            frame_overlay = bg_img.copy()
            clean_bg_path = os.path.join(ASSETS_DIR, "montealban.png")
            if os.path.exists(clean_bg_path):
                bg_img = Image.open(clean_bg_path).convert("RGBA").resize((target_width, target_height), Image.Resampling.LANCZOS)

        # 5. Escalar a la persona recortada proporcionalmente
        person_w, person_h = transparent_person_img.size
        new_person_h = int(target_height * 0.70) 
        ratio = new_person_h / float(person_h)
        new_person_w = int(person_w * ratio)
        
        person_resized = transparent_person_img.resize((new_person_w, new_person_h), Image.Resampling.LANCZOS)

        # 🌟 AURA / RESPLANDOR BLANCO ESTÉTICO Y ELEGANTE
        person_cv = cv2.cvtColor(np.array(person_resized), cv2.COLOR_RGBA2BGRA)
        alpha = person_cv[:, :, 3]

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
        dilated = cv2.dilate(alpha, kernel, iterations=1)
        halo_mask = cv2.GaussianBlur(dilated, (65, 65), 0)

        halo_layer = np.zeros_like(person_cv)
        halo_layer[:, :] = (255, 255, 255, 255)
        
        halo_alpha = cv2.subtract(halo_mask, alpha)
        halo_alpha = (halo_alpha * 0.95).astype(np.uint8) 
        halo_layer[:, :, 3] = halo_alpha

        base_person_canvas = Image.new("RGBA", person_resized.size, (0, 0, 0, 0))
        halo_pil = Image.fromarray(cv2.cvtColor(halo_layer, cv2.COLOR_BGRA2RGBA))
        
        base_person_canvas.paste(halo_pil, (0, 0), halo_pil)
        base_person_canvas.paste(person_resized, (0, 0), person_resized)

        # Posicionar centrado en la postal
        pos_x = (target_width - new_person_w) // 2
        pos_y = target_height - new_person_h - int(target_height * 0.05)

        bg_img.paste(base_person_canvas, (pos_x, pos_y), base_person_canvas)

        # 🌟 6. APLICAR MARCO SUPERIOR (Si aplica, limpiando el fondo negro central)
        if frame_overlay is not None:
            frame_np = np.array(frame_overlay)
            # Volver transparentes los píxeles negros del centro del marco
            black_pixels = (frame_np[:, :, 0] < 35) & (frame_np[:, :, 1] < 35) & (frame_np[:, :, 2] < 35)
            frame_np[black_pixels, 3] = 0 
            frame_transparent = Image.fromarray(frame_np, "RGBA")
            
            bg_img.paste(frame_transparent, (0, 0), frame_transparent)

        # 7. Estampar logo institucional
        logo_path = os.path.join(ASSETS_DIR, "logo1.png")
        if os.path.exists(logo_path):
            logo_img = Image.open(logo_path).convert("RGBA")
            logo_w = int(target_width * 0.15)
            logo_ratio = logo_w / float(logo_img.width)
            logo_h = int(float(logo_img.height) * float(logo_ratio))
            logo_resized = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

            margin = int(target_width * 0.03)
            bg_img.paste(logo_resized, (margin, target_height - logo_h - margin), logo_resized)

        # 8. Guardar salida final optimizada en alta calidad
        final_output = bg_img.convert("RGB")
        final_output.save(output_path, "JPEG", quality=95)
        
        print(f"🚀 Composición final de postal completada con éxito: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error en process_guelaguetza_ai con rembg: {e}")
        return False