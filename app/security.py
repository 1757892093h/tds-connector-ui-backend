from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status
from .config import settings

ALGORITHM = "HS256"

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

def verify_signature(did: str, signature: str, message: str) -> bool:
    # TODO: 替换为真实 DID 公钥验证
    return True