import sqlite3
from fastapi import APIRouter, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth_jwt import verify_token

router = APIRouter()
security = HTTPBearer()
DB_PATH = "../database/database.db"

def moderator_guard(credentials: HTTPAuthorizationCredentials):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload or payload.get("role") not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    return payload

@router.get("/api/moderator/listings/pending")
def get_pending_listings(credentials: HTTPAuthorizationCredentials = security):
    moderator_guard(credentials)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Title, CreatedAt FROM Listings WHERE Status = 'pending'")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "title": row[1], "created_at": row[2]} for row in rows]

@router.post("/api/moderator/listings/approve/{listing_id}")
def approve_listing(listing_id: int, credentials: HTTPAuthorizationCredentials = security):
    moderator_guard(credentials)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE Listings SET Status = 'approved' WHERE ID = ?", (listing_id,))
    conn.commit()
    conn.close()
    return {"message": "İlan onaylandı."}

@router.post("/api/moderator/listings/reject/{listing_id}")
def reject_listing(listing_id: int, credentials: HTTPAuthorizationCredentials = security):
    moderator_guard(credentials)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE Listings SET Status = 'rejected' WHERE ID = ?", (listing_id,))
    conn.commit()
    conn.close()
    return {"message": "İlan reddedildi."}
