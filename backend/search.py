import sqlite3
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()
DB_PATH = "../database/database.db"

@router.get("/api/search")
async def search(request: Request):
    params = request.query_params
    q = params.get("q", "")
    min_price = params.get("min", 0)
    max_price = params.get("max", 9999999)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Title, Description, Price FROM Listings
        WHERE (Title LIKE ? OR Description LIKE ?)
        AND Price >= ? AND Price <= ?
        ORDER BY CreatedAt DESC
    """, (f"%{q}%", f"%{q}%", min_price, max_price))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return JSONResponse(content=results)
