import sqlite3
from fastapi import APIRouter, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth_jwt import verify_token
from datetime import datetime

router = APIRouter()
security = HTTPBearer()
DB_PATH = "../database/database.db"

def admin_guard(credentials: HTTPAuthorizationCredentials):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Yalnızca admin erişebilir")
    return payload

@router.get("/api/admin/stats")
def get_admin_stats(credentials: HTTPAuthorizationCredentials = security):
    admin_guard(credentials)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Users")
    user_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Listings")
    listing_count = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(ViewCount) FROM Listings")
    view_count = cursor.fetchone()[0] or 0

    cursor.execute("SELECT Term, COUNT(*) as freq FROM SearchLogs GROUP BY Term ORDER BY freq DESC LIMIT 5")
    search_terms = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM Messages")
    msg_count = cursor.fetchone()[0]

    conn.close()

    return {
        "user_count": user_count,
        "listing_count": listing_count,
        "view_count": view_count,
        "top_searches": [{"term": t[0], "count": t[1]} for t in search_terms],
        "message_count": msg_count
    }

@router.get("/api/admin/listings/daily")
def daily_listing_graph(credentials: HTTPAuthorizationCredentials = security):
    admin_guard(credentials)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT DATE(CreatedAt) as date, COUNT(*) FROM Listings GROUP BY date ORDER BY date DESC LIMIT 10")
    data = cursor.fetchall()
    conn.close()

    # Son 10 günü tersine çevirip sırala
    return [{"date": row[0], "count": row[1]} for row in reversed(data)]
