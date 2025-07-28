import sqlite3, datetime
from fastapi import APIRouter, Request

router = APIRouter()
DB_PATH = "../database/database.db"

def log_action(user: str, action: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO Logs (User, Action, Timestamp) VALUES (?, ?, ?)", (user, action, timestamp))
    conn.commit()
    conn.close()

@router.get("/api/logs")
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Logs ORDER BY Timestamp DESC LIMIT 100")
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return logs

@router.get("/api/stats")
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    stats = {}

    cursor.execute("SELECT COUNT(*) FROM Listings")
    stats["total_listings"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Users")
    stats["total_users"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Listings WHERE IsFeatured = 1")
    stats["featured_listings"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Listings WHERE IsUrgent = 1")
    stats["urgent_listings"] = cursor.fetchone()[0]

    cursor.execute("SELECT DATE(Timestamp), COUNT(*) FROM Logs GROUP BY DATE(Timestamp) ORDER BY DATE(Timestamp) DESC LIMIT 7")
    stats["logs_per_day"] = cursor.fetchall()

    conn.close()
    return stats
