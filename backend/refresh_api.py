import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from refresh_jwt import verify_refresh_token
from auth_jwt import create_access_token

router = APIRouter()
DB_PATH = "../database/database.db"

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/api/token/refresh")
def refresh_access_token(request: RefreshRequest):
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş refresh token.")

    # Refresh token geçerliyse yeni access token ver
    new_access_token = create_access_token({"email": payload["email"], "role": payload["role"]})
    return {"access_token": new_access_token}
