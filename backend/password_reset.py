import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.hash import sha256_crypt

router = APIRouter()
DB_PATH = "../database/database.db"

class ResetRequest(BaseModel):
    email: str
    new_password: str

@router.post("/api/reset-password")
async def reset_password(request: ResetRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (request.email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    hashed = sha256_crypt.hash(request.new_password)
    cursor.execute("UPDATE Users SET Password = ? WHERE Id = ?", (hashed, user[0]))
    conn.commit()
    conn.close()
    return {"message": "Şifre sıfırlandı"}
