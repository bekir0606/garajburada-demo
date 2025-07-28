import sqlite3
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth_jwt import verify_token

router = APIRouter()
security = HTTPBearer()
DB_PATH = "../database/database.db"

def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    return payload["user_id"]

@router.post("/api/car/add")
async def add_car(request: Request, user_id: int = Depends(get_user_id)):
    body = await request.json()
    plate = body.get("plate")
    brand = body.get("brand")
    model = body.get("model")
    year = body.get("year")
    if not plate:
        raise HTTPException(status_code=400, detail="Plaka zorunlu")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Cars (UserID, Plate, Brand, Model, Year) VALUES (?, ?, ?, ?, ?)",
                   (user_id, plate, brand, model, year))
    conn.commit()
    conn.close()
    return {"message": "Araç eklendi."}

@router.post("/api/car/maintenance")
async def add_maintenance(request: Request, user_id: int = Depends(get_user_id)):
    body = await request.json()
    car_id = body.get("car_id")
    type = body.get("type")  # örnek: "yağ değişimi", "lastik", "fren"
    date = body.get("date")
    note = body.get("note", "")
    if not car_id or not type or not date:
        raise HTTPException(status_code=400, detail="Eksik bilgi")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Maintenance (CarID, Type, Date, Note) VALUES (?, ?, ?, ?)",
                   (car_id, type, date, note))
    conn.commit()
    conn.close()
    return {"message": "Bakım kaydedildi."}

@router.post("/api/car/insurance")
async def add_insurance(request: Request, user_id: int = Depends(get_user_id)):
    body = await request.json()
    car_id = body.get("car_id")
    company = body.get("company")
    policy_no = body.get("policy_no")
    valid_until = body.get("valid_until")
    if not car_id or not company or not valid_until:
        raise HTTPException(status_code=400, detail="Eksik bilgi")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Insurance (CarID, Company, PolicyNo, ValidUntil) VALUES (?, ?, ?, ?)",
                   (car_id, company, policy_no, valid_until))
    conn.commit()
    conn.close()
    return {"message": "Sigorta kaydedildi."}
