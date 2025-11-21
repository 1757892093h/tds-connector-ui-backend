from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_session
from ..deps import get_current_user
from ..models import User
from ..schemas import AuthResponse, LoginRequest, RegisterRequest, TokenVerifyResponse
from ..security import create_access_token, verify_signature

router = APIRouter(prefix=f"{settings.api_prefix}/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_session)):
    """基于 DID 的注册流程：验证签名 → 写入用户 → 返回 JWT。"""
    message = f"Register:{payload.did}"
    if not verify_signature(payload.did, payload.signature, message):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    existing_user = await session.execute(select(User).where(User.did == payload.did))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="DID already registered")

    user = User(did=payload.did, username=payload.username, email=payload.email)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token({"sub": user.id, "did": user.did})
    return {
        "token": token,
        "user": {
            "id": user.id,
            "did": user.did,
            "username": user.username,
            "email": user.email,
        },
    }


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    """基于 DID 的登录流程：查找用户 → 验签 → 返回 JWT。"""
    result = await session.execute(select(User).where(User.did == payload.did))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DID not found")

    message = f"Login:{payload.did}"
    if not verify_signature(payload.did, payload.signature, message):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    token = create_access_token({"sub": user.id, "did": user.did})
    return {
        "token": token,
        "user": {
            "id": user.id,
            "did": user.did,
            "username": user.username,
            "email": user.email,
        },
    }


@router.get("/verify", response_model=TokenVerifyResponse)
async def verify_user(current_user: User = Depends(get_current_user)):
    """严格的 token 校验：必须提供合法 Bearer Token，否则返回 401。"""
    return {
        "id": current_user.id,
        "did": current_user.did,
        "username": current_user.username,
        "email": current_user.email,
    }