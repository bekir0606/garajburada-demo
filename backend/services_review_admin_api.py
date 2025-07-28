import sqlite3
from fastapi import APIRouter, HTTPException, Depends
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

@router.delete("/api/services/review/delete/{review_id}")
async def delete_review(review_id: int, admin: dict = Depends(get_admin)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ServiceReviews WHERE rowid = ?", (review_id,))
    conn.commit()
    conn.close()
    return {"message": f"Yorum ID {review_id} silindi."}
