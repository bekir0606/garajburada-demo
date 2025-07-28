import sqlite3
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth_jwt import verify_token

router = APIRouter()
DB_PATH = "../database/database.db"
security = HTTPBearer()

def get_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    return payload

@router.post("/api/services/add")
async def add_service(request: Request, admin: dict = Depends(get_admin)):
    data = await request.json()
    name = data.get("name")
    lat = data.get("lat")
    lon = data.get("lon")
    type = data.get("type", "Genel")
    if not all([name, lat, lon]):
        raise HTTPException(status_code=400, detail="Eksik bilgi")

    try:
        lat = float(lat)
        lon = float(lon)
    except:
        raise HTTPException(status_code=400, detail="Koordinatlar sayı olmalı")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Services (Name, Latitude, Longitude, Type) VALUES (?, ?, ?, ?)",
                   (name, lat, lon, type))
    conn.commit()
    conn.close()
    return {"message": f"Servis noktası eklendi: {name}"}

import sqlite3
from fastapi import APIRouter

router = APIRouter()
DB_PATH = "../database/database.db"

@router.get("/api/services")
async def list_services():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Name, Latitude, Longitude, Type FROM Services")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "lat": r[2], "lon": r[3], "type": r[4]} for r in rows]
