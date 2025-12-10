import json  # ✅ 添加此行

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_session
from ..deps import get_current_user
from ..models import Connector, DataOffering, PolicyTemplate, ContractTemplate
from ..schemas import (
    DataOfferingCreate, 
    DataOfferingOut, 
    DataOfferingWithCountsOut,
    DataOfferingDetailOut, 
    PolicyTemplateOut, 
    ContractTemplateOut
)

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


@router.get("", response_model=list[DataOfferingWithCountsOut])
async def list_offerings(
      connector_id: str | None = None,
      data_space_id: str | None = None,  # 按数据空间过滤
      public: bool = False,  # 是否返回所有公开的 offerings（用于数据目录）
      exclude_self: bool = False,  # 公共视图下是否排除当前用户自己的提供者连接器
      session: AsyncSession = Depends(get_session),
      current_user=Depends(get_current_user),
  ):
      # 如果 public=True，返回所有 offerings（用于数据消费页面的数据目录）
      if public:
          query = select(DataOffering).join(Connector)
          # 按数据空间过滤（如果提供）
          if data_space_id:
              query = query.where(Connector.data_space_id == data_space_id)
          # 按连接器过滤（如果提供）
          if connector_id:
              query = query.where(DataOffering.connector_id == connector_id)
          # 排除当前用户自己的提供者连接器（消费者视角不应看到自己的提供数据）
          if exclude_self:
              query = query.where(Connector.owner_user_id != current_user.id)
      else:
          # 默认行为：只返回当前用户拥有的连接器的 offerings（用于数据提供页面）
          query = select(DataOffering).join(Connector).where(Connector.owner_user_id == current_user.id)
          # 按数据空间过滤（如果提供）
          if data_space_id:
              query = query.where(Connector.data_space_id == data_space_id)
          # 按连接器过滤（如果提供）
          if connector_id:
              query = query.where(DataOffering.connector_id == connector_id)
      # 使用 selectinload 加载连接器及其策略/模板（用于获取数量）
      query = query.options(
          selectinload(DataOffering.connector).selectinload(Connector.policy_templates),
          selectinload(DataOffering.connector).selectinload(Connector.contract_templates)
      )
      result = await session.execute(query)
      offerings = result.scalars().all()
      
      # 转换为包含数量的响应模型
      return [
          DataOfferingWithCountsOut(
              id=offering.id,
              connector_id=offering.connector_id,
              title=offering.title,
              description=offering.description,
              data_type=offering.data_type,
              access_policy=offering.access_policy,
              storage_meta=offering.storage_meta,
              registration_status=offering.registration_status,
              created_at=offering.created_at,
              policy_templates_count=len(offering.connector.policy_templates) if offering.connector else 0,
              contract_templates_count=len(offering.connector.contract_templates) if offering.connector else 0,
          )
          for offering in offerings
      ]


@router.get("/{offering_id}", response_model=DataOfferingDetailOut)
async def get_offering(
      offering_id: str,
      session: AsyncSession = Depends(get_session),
      current_user=Depends(get_current_user),
  ):
      # 获取数据资源详情
      result = await session.execute(
          select(DataOffering).where(DataOffering.id == offering_id)
      )
      offering = result.scalar_one_or_none()
      if not offering:
          raise HTTPException(status_code=404, detail="Data offering not found")

      # 获取提供者连接器的策略模板和合约模板
      connector_result = await session.execute(
          select(Connector)
          .options(
              selectinload(Connector.policy_templates).selectinload(PolicyTemplate.rules),
              selectinload(Connector.contract_templates).selectinload(ContractTemplate.policy_templates).selectinload(PolicyTemplate.rules)
          )
          .where(Connector.id == offering.connector_id)
      )
      connector = connector_result.scalar_one_or_none()
      
      if not connector:
          raise HTTPException(status_code=404, detail="Connector not found")

      # 构建详情响应，包含策略模板和合约模板
      return DataOfferingDetailOut(
          id=offering.id,
          connector_id=offering.connector_id,
          title=offering.title,
          description=offering.description,
          data_type=offering.data_type,
          access_policy=offering.access_policy,
          storage_meta=offering.storage_meta,
          registration_status=offering.registration_status,
          created_at=offering.created_at,
          policy_templates=[PolicyTemplateOut.model_validate(pt) for pt in connector.policy_templates],
          contract_templates=[ContractTemplateOut.model_validate(ct) for ct in connector.contract_templates],
      )