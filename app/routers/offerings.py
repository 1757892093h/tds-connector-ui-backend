import json  # ✅ 添加此行

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_session
from ..deps import get_current_user
from ..models import Connector, DataOffering
from ..schemas import DataOfferingCreate, DataOfferingOut

router = APIRouter(prefix=settings.api_prefix + "/offerings", tags=["offerings"])


@router.post("", response_model=DataOfferingOut)
async def create_offering(
      connector_id: str = Form(...),
      title: str = Form(...),
      description: str = Form(...),
      data_type: str = Form(...),
      access_policy: str = Form(...),
      storage_meta: str = Form(...),
      file: UploadFile | None = File(None),
      session: AsyncSession = Depends(get_session),
      current_user=Depends(get_current_user),
  ):
      result = await session.execute(select(Connector).where(Connector.id == connector_id))
      connector = result.scalar_one_or_none()
      if not connector or connector.owner_user_id != current_user.id:
          raise HTTPException(status_code=404, detail="Connector not found")

      # 如果上传了文件，可以在这里处理
      # if file:
      #     file_content = await file.read()
      #     # 保存文件或上传到云存储

      offering = DataOffering(
          connector_id=connector.id,
          title=title,
          description=description,
          data_type=data_type,
          access_policy=access_policy,
          storage_meta=json.loads(storage_meta),
          registration_status="unregistered",
      )
      session.add(offering)
      await session.commit()
      await session.refresh(offering)
      return offering


@router.get("", response_model=list[DataOfferingOut])
async def list_offerings(
      connector_id: str | None = None,
      session: AsyncSession = Depends(get_session),
      current_user=Depends(get_current_user),
  ):
      query = select(DataOffering).join(Connector).where(Connector.owner_user_id == current_user.id)
      if connector_id:
          query = query.where(DataOffering.connector_id == connector_id)
      result = await session.execute(query)
      offerings = result.scalars().all()
      return offerings