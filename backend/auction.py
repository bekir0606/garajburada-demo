import sqlite3, datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
DB_PATH = "../database/database.db"

class StartAuction(BaseModel):
    listing_id: int
    starting_price: float
    duration_minutes: int

class BidRequest(BaseModel):
    auction_id: int
    bidder_email: str
    bid_amount: float

@router.post("/api/auction/start")
def start_auction(req: StartAuction):
    end_time = (datetime.datetime.now() + datetime.timedelta(minutes=req.duration_minutes)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Auctions (ListingId, CurrentPrice, EndTime) VALUES (?, ?, ?)",
                   (req.listing_id, req.starting_price, end_time))
    conn.commit()
    conn.close()
    return {"message": "Açık artırma başlatıldı"}

@router.post("/api/auction/bid")
def place_bid(req: BidRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (req.bidder_email,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    cursor.execute("SELECT CurrentPrice, EndTime FROM Auctions WHERE Id = ?", (req.auction_id,))
    auction = cursor.fetchone()
    if not auction:
        raise HTTPException(status_code=404, detail="Açık artırma bulunamadı.")

    if datetime.datetime.now() > datetime.datetime.fromisoformat(auction[1]):
        raise HTTPException(status_code=400, detail="Açık artırma sona ermiş.")

    if req.bid_amount <= auction[0]:
        raise HTTPException(status_code=400, detail="Teklif mevcut fiyattan yüksek olmalı.")

    cursor.execute("UPDATE Auctions SET CurrentPrice = ?, LastBidderId = ? WHERE Id = ?",
                   (req.bid_amount, user[0], req.auction_id))
    conn.commit()
    conn.close()
    return {"message": "Teklif verildi"}

@router.get("/api/auction/active")
def get_auctions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    cursor.execute("SELECT * FROM Auctions WHERE EndTime > ?", (now,))
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result
