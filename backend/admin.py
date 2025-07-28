import sqlite3
from fastapi import APIRouter

router = APIRouter()
DB_PATH = "../database/database.db"

@router.get("/api/admin/listings")
async def get_all_listings():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT L.Title, L.Price, U.Email
        FROM Listings L
        JOIN Users U ON L.UserId = U.Id
        ORDER BY L.CreatedAt DESC
    """)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

@router.get("/api/admin/users")
async def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT Email, Role FROM Users ORDER BY Id DESC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users
