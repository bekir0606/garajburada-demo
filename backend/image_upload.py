import os
import shutil
import sqlite3
from fastapi import APIRouter, UploadFile, Form, HTTPException

router = APIRouter()
DB_PATH = "../database/database.db"
UPLOAD_DIR = "../frontend/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/api/upload")
async def upload_image(email: str = Form(...), listing_id: int = Form(...), file: UploadFile = Form(...)):
    try:
        filename = f"{email.replace('@','_')}_{listing_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Veritabanına yol kaydı yapılabilir (şimdilik dosya kaydı yapılıyor)
        return {"message": "Fotoğraf yüklendi", "file": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
