import sqlite3
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth_jwt import verify_token

router = APIRouter()
DB_PATH = "../database/database.db"
security = HTTPBearer()

def get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Token geçersiz")
    return payload["user_id"]

@router.post("/api/services/review")
async def add_review(request: Request, user_id: int = Depends(get_user)):
    data = await request.json()
    service_id = data.get("service_id")
    rating = data.get("rating")
    comment = data.get("comment", "")
    if not service_id or rating is None:
        raise HTTPException(status_code=400, detail="Eksik veri")
    if not (1 <= int(rating) <= 5):
        raise HTTPException(status_code=400, detail="Puan 1 ile 5 arasında olmalı")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ServiceReviews (ServiceID, UserID, Rating, Comment) VALUES (?, ?, ?, ?)",
                   (service_id, user_id, rating, comment))
    conn.commit()
    conn.close()
    return {"message": "Yorum ve puan kaydedildi."}

@router.get("/api/services/reviews/{service_id}")
async def get_reviews(service_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT Rating, Comment FROM ServiceReviews WHERE ServiceID = ?", (service_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"rating": r[0], "comment": r[1]} for r in rows]
