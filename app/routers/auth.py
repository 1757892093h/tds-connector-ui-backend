from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
from ..schemas import RegisterRequest, LoginRequest, AuthResponse
from ..security import verify_signature, create_access_token
from ..database import get_session
from ..models import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, session: AsyncSession = Depends(get_session)):
    message = f"Register:{request.did}"
    if not verify_signature(request.did, request.signature, message):
        raise HTTPException(status_code=401, detail="Invalid signature")

    existing = await session.get(User, request.did)
    if existing:
        raise HTTPException(status_code=400, detail="DID already registered")

    user = User(did=request.did, did_document=json.dumps(request.didDocument))
    session.add(user)
    await session.commit()

    token = create_access_token(request.did)
    return {"token": token, "user": {"did": request.did}}

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, request.did)
    if not user:
        raise HTTPException(status_code=404, detail="DID not found")

    message = f"Login:{request.did}"
    if not verify_signature(request.did, request.signature, message):
        raise HTTPException(status_code=401, detail="Invalid signature")

    token = create_access_token(request.did)
    return {"token": token, "user": {"did": request.did}}

@router.get("/verify")
async def verify_user(user=Depends(lambda: None)):
    # 实际使用 get_current_user 依赖; 为简洁起见，前端调用时由路由中使用
    return {"status": "ok"}