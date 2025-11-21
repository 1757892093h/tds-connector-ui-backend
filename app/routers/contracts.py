from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_session
from ..deps import get_current_user
from ..models import Connector, Contract
from ..schemas import ContractCreate, ContractOut

router = APIRouter(prefix=settings.api_prefix + "/contracts", tags=["contracts"])


@router.post("", response_model=ContractOut)
async def create_contract(
      payload: ContractCreate,
      session: AsyncSession = Depends(get_session),
      current_user=Depends(get_current_user),
  ):
      # Provider must belong to current user
      result = await session.execute(select(Connector).where(Connector.id == payload.provider_connector_id))
      provider = result.scalar_one_or_none()
      if not provider or provider.owner_user_id != current_user.id:
          raise HTTPException(status_code=404, detail="Provider connector not found or not owned by you")

      # Consumer exists?
      result = await session.execute(select(Connector).where(Connector.id == payload.consumer_connector_id))
      consumer = result.scalar_one_or_none()
      if not consumer:
          raise HTTPException(status_code=404, detail="Consumer connector not found")

      contract = Contract(
          name=payload.name,
          policy=payload.policy,
          status=payload.status or "active",
          contract_address=payload.contract_address,
          expires_at=payload.expires_at,
          provider_connector_id=provider.id,
          consumer_connector_id=consumer.id,
      )
      session.add(contract)
      await session.commit()
      await session.refresh(contract)
      return contract


@router.get("", response_model=list[ContractOut])
async def list_contracts(
      connector_id: str | None = None,
      role: str | None = None,  # provider / consumer
      session: AsyncSession = Depends(get_session),
      current_user=Depends(get_current_user),
  ):
      # 获取当前用户拥有的所有连接器ID
      user_connectors_result = await session.execute(
          select(Connector.id).where(Connector.owner_user_id == current_user.id)
      )
      user_connector_ids = [row[0] for row in user_connectors_result.fetchall()]

      if not user_connector_ids:
          return []

      # 构建基础查询：用户作为 provider 或 consumer 的所有合约
      query = select(Contract).where(
          or_(
              Contract.provider_connector_id.in_(user_connector_ids),
              Contract.consumer_connector_id.in_(user_connector_ids)
          )
      )

      # 如果指定了 connector_id 和 role，进一步过滤
      if connector_id:
          # 验证 connector_id 属于当前用户
          if connector_id not in user_connector_ids:
              raise HTTPException(status_code=403, detail="Connector does not belong to you")

          if role == "consumer":
              query = query.where(Contract.consumer_connector_id == connector_id)
          elif role == "provider":
              query = query.where(Contract.provider_connector_id == connector_id)
          else:
              # 如果没有指定角色，返回该连接器作为 provider 或 consumer 的所有合约
              query = query.where(
                  or_(
                      Contract.provider_connector_id == connector_id,
                      Contract.consumer_connector_id == connector_id
                  )
              )

      result = await session.execute(query)
      contracts = result.scalars().all()
      return contracts