import time
import jwt

REFRESH_SECRET = "refreshsupersecret"
ALGORITHM = "HS256"
REFRESH_EXPIRY_SECONDS = 7 * 24 * 60 * 60  # 7 gün

def create_refresh_token(data: dict):
    payload = data.copy()
    payload["exp"] = time.time() + REFRESH_EXPIRY_SECONDS
    return jwt.encode(payload, REFRESH_SECRET, algorithm=ALGORITHM)

def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, REFRESH_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
