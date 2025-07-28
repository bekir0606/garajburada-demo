import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
DB_PATH = "../database/database.db"

class FavoriteRequest(BaseModel):
    email: str
    listing_id: int

@router.post("/api/favorites")
async def add_favorite(request: FavoriteRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (request.email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    cursor.execute("INSERT INTO Favorites (UserId, ListingId) VALUES (?, ?)", (user[0], request.listing_id))
    conn.commit()
    conn.close()
    return {"message": "Favoriye eklendi"}

@router.get("/api/favorites/{email}")
async def get_favorites(email: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT L.Title, L.Description, L.Price
        FROM Favorites F
        JOIN Listings L ON F.ListingId = L.Id
        JOIN Users U ON F.UserId = U.Id
        WHERE U.Email = ?
        ORDER BY F.Id DESC
    """, (email,))
    favorites = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return favorites
