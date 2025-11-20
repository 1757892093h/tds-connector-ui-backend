from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .security import verify_token

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    user_did = verify_token(credentials.credentials)
    if not user_did:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return {"did": user_did}