from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from pdf2image import convert_from_bytes
from PIL import Image
from pathlib import Path
from pypdf import PdfWriter
from fastapi.responses import FileResponse

import io
import pytesseract

UPLOAD_DIR = Path("uploads/ocr")
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter()

@router.get("/tesseract/", tags=["tesseract"])
async def get_tesseract():
    return { 'version': str(pytesseract.get_tesseract_version()), 'langs': pytesseract.get_languages(config='')}

def image_to_text(image, lang='eng'):
    text = pytesseract.image_to_string(image, lang=lang)
    return text

@router.post("/tesseract/image-to-string", tags=["tesseract"])
async def image_to_string(image_file: UploadFile = File(...)):
    try:
        image_content = await image_file.read()
        img = Image.open(io.BytesIO(image_content))
        result_text = image_to_text(img, lang='jpn')

        return {'result': result_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tesseract/pdf-to-text", tags=["tesseract"])
async def pdf_to_text(pdf_file: UploadFile = File(...)):
    try:
        # Membaca konten file PDF
        pdf_content = await pdf_file.read()

        # Konversi halaman PDF menjadi gambar (PNG)
        images = convert_from_bytes(pdf_content)

        # Proses setiap gambar dengan Tesseract OCR
        extracted_text = []
        for img in images:
            # Konversi gambar PIL ke dalam format RGBA (diperlukan oleh Tesseract)
            img_rgba = img.convert("RGBA")

            # Dapatkan teks dari gambar menggunakan Tesseract (bahasa Jepang)
            text = image_to_text(img_rgba, lang='jpn')
            extracted_text.append(text)

        return {"extracted_text": extracted_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tesseract/pdf-to-ocr", tags=["tesseract"])
async def pdf_to_ocrpdf(pdf_file: UploadFile = File(...)):
    try:
        file_location = UPLOAD_DIR / pdf_file.filename
        pdf_content = await pdf_file.read()

        images = convert_from_bytes(pdf_content)

        merger = PdfWriter()

        for i, img in enumerate(images):
            pdf = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang='jpn')
            merger.append(io.BytesIO(pdf))

        with open(file_location, 'wb') as f:
            merger.write(f)

        merger.close()

        return {"document": "http://localhost:8004/" + f'{file_location}'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
