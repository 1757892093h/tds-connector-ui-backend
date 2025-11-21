from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from .database import get_session
from .models import User
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
      token: str = Depends(oauth2_scheme),
      session: AsyncSession = Depends(get_session),
  ) -> User:
      credentials_exception = HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Could not validate credentials",
          headers={"WWW-Authenticate": "Bearer"},
      )

      try:
          payload = decode_access_token(token)
      except jwt.ExpiredSignatureError:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Token has expired",
              headers={"WWW-Authenticate": "Bearer"},
          )
      except jwt.InvalidTokenError:
          raise credentials_exception

      user_id: str | None = payload.get("sub")
      if not user_id:
          raise credentials_exception

      result = await session.execute(select(User).where(User.id == user_id))
      user = result.scalar_one_or_none()

      if not user:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="User not found"
          )

      return user