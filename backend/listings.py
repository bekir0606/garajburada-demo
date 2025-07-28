import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
DB_PATH = "../database/database.db"

class ListingRequest(BaseModel):
    is_featured: bool = False
    is_urgent: bool = False
    email: str
    title: str
    description: str
    price: float

@router.get("/api/listings")
async def get_listings():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT Title, Description, Price FROM Listings ORDER BY CreatedAt DESC")
    listings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return listings

@router.post("/api/listings")
async def add_listing(request: ListingRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (request.email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    cursor.execute("INSERT INTO Listings (UserId, Title, Description, Price, IsFeatured, IsUrgent) VALUES (?, ?, ?, ?, ?, ?)",
                   (user[0], request.title, request.description, request.price, int(request.is_featured), int(request.is_urgent)))
    conn.commit()
    conn.close()
    return {"message": "İlan eklendi."}


@router.get("/api/listings/featured")
async def get_featured_listings():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT Title, Price FROM Listings WHERE IsFeatured = 1 ORDER BY CreatedAt DESC")
    featured = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return featured

@router.get("/api/listings/urgent")
async def get_urgent_listings():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT Title, Price FROM Listings WHERE IsUrgent = 1 ORDER BY CreatedAt DESC")
    urgent = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return urgent
