import time
import jwt

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 3600

def create_access_token(data: dict):
    payload = data.copy()  # role dahil edilebilir
    payload["exp"] = time.time() + TOKEN_EXPIRY_SECONDS
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
