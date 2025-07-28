from fastapi import APIRouter, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth_jwt import verify_token

router = APIRouter()
security = HTTPBearer()

@router.get("/api/admin/protected")
def admin_only(credentials: HTTPAuthorizationCredentials = security):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Yetkisiz erişim.")
    return {"message": f"Hoş geldin Admin: {payload['email']}"}
