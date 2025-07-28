import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
DB_PATH = "../database/database.db"

class PaymentRequest(BaseModel):
    email: str
    listing_id: int
    type: str  # vitrin / acil

@router.post("/api/payment")
async def process_payment(request: PaymentRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (request.email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    if request.type == "vitrin":
        cursor.execute("UPDATE Listings SET IsFeatured = 1 WHERE Id = ? AND UserId = ?", (request.listing_id, user[0]))
        conn.commit()
        message = "Vitrin ilan aktif edildi."
    elif request.type == "acil":
        cursor.execute("UPDATE Listings SET IsUrgent = 1 WHERE Id = ? AND UserId = ?", (request.listing_id, user[0]))
        conn.commit()
        message = "Acil ilan aktif edildi."
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Geçersiz ilan tipi")

    conn.close()
    return {"message": message}
