import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.hash import sha256_crypt
from auth_jwt import create_access_token
from refresh_jwt import create_refresh_token

router = APIRouter()
DB_PATH = "../database/database.db"

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/api/register")
def register(user: UserRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Users WHERE Email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı.")

    hashed_password = sha256_crypt.hash(user.password)
    cursor.execute("INSERT INTO Users (Name, Email, Password) VALUES (?, ?, ?)", (user.name, user.email, hashed_password))
    conn.commit()
    conn.close()
    return {"message": "Kayıt başarılı."}

@router.post("/api/login")
def login(user: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Users WHERE Email = ?", (user.email,))
    result = cursor.fetchone()
    conn.close()

    if not result or not sha256_crypt.verify(user.password, result[3]):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")

    token = create_access_token({"email": result[2], "role": result[4]})
    refresh_token = create_refresh_token({"email": result[2], "role": result[4]})
    return {"access_token": token, "refresh_token": refresh_token}
