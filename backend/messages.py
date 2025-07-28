import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
DB_PATH = "../database/database.db"

class MessageRequest(BaseModel):
    from_email: str
    to_email: str
    listing_id: int
    message: str

@router.post("/api/messages")
async def send_message(request: MessageRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (request.from_email,))
    from_user = cursor.fetchone()
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (request.to_email,))
    to_user = cursor.fetchone()

    if not from_user or not to_user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    cursor.execute("""INSERT INTO Messages (FromUserId, ToUserId, ListingId, Message)
                      VALUES (?, ?, ?, ?)""", (from_user[0], to_user[0], request.listing_id, request.message))
    conn.commit()
    conn.close()
    return {"message": "Mesaj gönderildi."}

@router.get("/api/messages")
async def get_messages():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT M.Message, U1.Email as FromEmail, U2.Email as ToEmail
        FROM Messages M
        JOIN Users U1 ON M.FromUserId = U1.Id
        JOIN Users U2 ON M.ToUserId = U2.Id
        ORDER BY M.SentAt DESC
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result
