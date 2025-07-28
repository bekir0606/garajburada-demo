
import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.hash import sha256_crypt
from auth_jwt import create_access_token

router = APIRouter()

DB_PATH = "../database/database.db"

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/api/login")
async def login(request: LoginRequest):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT Password FROM Users WHERE Email = ?", (request.email,))
        row = cursor.fetchone()
        conn.close()

        if row and sha256_crypt.verify(request.password, row[0]):
            return {"message": "Giriş başarılı"}
        else:
            raise HTTPException(status_code=401, detail="Hatalı email ya da şifre")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RegisterRequest(BaseModel):
    email: str
    password: str

@router.post("/api/register")
async def register(request: RegisterRequest):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT Id FROM Users WHERE Email = ?", (request.email,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı.")

        hashed_password = sha256_crypt.hash(request.password)
        cursor.execute("INSERT INTO Users (Email, Password, Role) VALUES (?, ?, ?)",
                       (request.email, hashed_password, "BireyselÜye"))
        conn.commit()
        conn.close()
        return {"message": "Kayıt başarılı"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
