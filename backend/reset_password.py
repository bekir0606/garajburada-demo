import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.hash import sha256_crypt
from email_service import send_email

router = APIRouter()
DB_PATH = "../database/database.db"

class ResetRequest(BaseModel):
    email: str
    new_password: str

@router.post("/api/reset-password")
def reset_password(request: ResetRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Kullanıcıyı bul
    cursor.execute("SELECT * FROM Users WHERE Email = ?", (request.email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    # Şifreyi güncelle
    hashed_password = sha256_crypt.hash(request.new_password)
    cursor.execute("UPDATE Users SET Password = ? WHERE Email = ?", (hashed_password, request.email))
    conn.commit()
    conn.close()

    # E-posta bildirimi gönder
    send_email(request.email, "Şifre Güncellendi", f"Merhaba,<br><br>Şifreniz başarıyla <b>güncellendi</b>.<br><br>Yeni şifreniz: {request.new_password}")

    return {"message": "Şifre başarıyla güncellendi."}
