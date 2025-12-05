from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_session
from ..deps import get_current_user
from ..models import Connector, Contract, ContractTemplate, DataOffering, DataRequest
from ..schemas import ContractCreate, ContractOut, ContractConfirm

router = APIRouter(prefix=settings.api_prefix + "/contracts", tags=["contracts"])


@router.post("", response_model=ContractOut)
async def create_contract(
      payload: ContractCreate,
      session: AsyncSession = Depends(get_session),
      current_user=Depends(get_current_user),
  ):
      """创建数据合约（基于请求和模板）
      
      注意：只有提供者（provider）可以创建合约。
      - provider_connector_id 必须属于当前用户
      - consumer_connector_id 可以是任何用户的连接器（只需要存在）
      """
      # 验证提供者连接器属于当前用户
      result = await session.execute(
          select(Connector).where(Connector.id == payload.provider_connector_id)
      )
      provider = result.scalar_one_or_none()
      if not provider:
          raise HTTPException(
              status_code=404,
              detail="Provider connector not found"
          )
      if provider.owner_user_id != current_user.id:
          raise HTTPException(
              status_code=403,
              detail=f"Provider connector does not belong to you. Only the provider can create contracts."
          )

      # 验证消费者连接器存在（可以是任何用户的）
      result = await session.execute(
          select(Connector).where(Connector.id == payload.consumer_connector_id)
      )
      consumer = result.scalar_one_or_none()
      if not consumer:
          raise HTTPException(
              status_code=404, 
              detail="Consumer connector not found"
          )
      
      # 防止自己和自己创建合约（可选，根据业务需求）
      if provider.id == consumer.id:
          raise HTTPException(
              status_code=400,
              detail="Provider and consumer cannot be the same connector"
          )

      # 验证合约模板
      result = await session.execute(
          select(ContractTemplate).where(ContractTemplate.id == payload.contract_template_id)
      )
      contract_template = result.scalar_one_or_none()
      if not contract_template:
          raise HTTPException(status_code=404, detail="Contract template not found")

      # 验证合约模板属于提供者
      if contract_template.connector_id != payload.provider_connector_id:
          raise HTTPException(
              status_code=403,
              detail="Contract template does not belong to the provider connector"
          )

      # 验证数据资源
      result = await session.execute(
          select(DataOffering).where(DataOffering.id == payload.data_offering_id)
      )
      data_offering = result.scalar_one_or_none()
      if not data_offering:
          raise HTTPException(status_code=404, detail="Data offering not found")

      # 验证数据资源属于提供者
      if data_offering.connector_id != payload.provider_connector_id:
          raise HTTPException(
              status_code=403,
              detail="Data offering does not belong to the provider connector"
          )

      # 如果提供了数据请求ID，验证
      data_request = None
      if payload.data_request_id:
          result = await session.execute(
              select(DataRequest).where(DataRequest.id == payload.data_request_id)
          )
          data_request = result.scalar_one_or_none()
          if not data_request:
              raise HTTPException(status_code=404, detail="Data request not found")

          # 验证请求状态
          if data_request.status != "approved":
              raise HTTPException(
                  status_code=400,
                  detail="Data request must be approved before creating contract"
              )

          # 验证请求的数据资源和消费者匹配
          if data_request.data_offering_id != payload.data_offering_id:
              raise HTTPException(
                  status_code=400,
                  detail="Data request does not match data offering"
              )
          if data_request.consumer_connector_id != payload.consumer_connector_id:
              raise HTTPException(
                  status_code=400,
                  detail="Data request does not match consumer connector"
              )

          # 更新请求状态为已完成
          data_request.status = "completed"
          data_request.updated_at = datetime.now(timezone.utc)

      # 创建合约
      contract = Contract(
          name=payload.name,
          status="pending_consumer",  # 等待消费者确认
          provider_connector_id=provider.id,
          consumer_connector_id=consumer.id,
          contract_template_id=contract_template.id,
          data_offering_id=data_offering.id,
          data_request_id=payload.data_request_id,
          expires_at=payload.expires_at,
      )
      session.add(contract)

      # 更新合约模板使用次数
      contract_template.usage_count += 1

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


@router.put("/{contract_id}/confirm", response_model=ContractOut)
async def confirm_contract(
    contract_id: str,
    payload: ContractConfirm,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """消费者确认或拒绝合约"""
    # 查找合约
    result = await session.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # 验证是消费者
    result = await session.execute(
        select(Connector).where(Connector.id == contract.consumer_connector_id)
    )
    consumer_connector = result.scalar_one_or_none()

    if not consumer_connector or consumer_connector.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the consumer can confirm or reject this contract"
        )

    # 检查状态
    if contract.status != "pending_consumer":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm contract with status: {contract.status}"
        )

    # 更新状态
    if payload.action == "confirm":
        contract.status = "active"
    elif payload.action == "reject":
        contract.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    contract.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(contract)
    return contract


@router.post("/{contract_id}/deploy")
async def deploy_contract_to_blockchain(
    contract_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """部署合约到区块链（模拟）"""
    # 查找合约
    result = await session.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # 验证权限（提供者或消费者）
    result = await session.execute(
        select(Connector).where(
            or_(
                Connector.id == contract.provider_connector_id,
                Connector.id == contract.consumer_connector_id
            )
        )
    )
    connectors = result.scalars().all()
    user_connector_ids = [c.id for c in connectors if c.owner_user_id == current_user.id]

    if not user_connector_ids:
        raise HTTPException(status_code=403, detail="Access denied")

    # 检查状态
    if contract.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Contract must be active to deploy to blockchain"
        )

    # 检查是否已部署
    if contract.contract_address:
        raise HTTPException(
            status_code=400,
            detail="Contract already deployed to blockchain"
        )

    # 模拟部署到区块链
    # 在实际实现中，这里会调用区块链API
    import hashlib
    import time

    # 生成模拟的合约地址和交易哈希
    timestamp = str(time.time())
    contract_address = "0x" + hashlib.sha256(
        f"{contract.id}{timestamp}".encode()
    ).hexdigest()[:40]

    blockchain_tx_id = "0x" + hashlib.sha256(
        f"tx{contract.id}{timestamp}".encode()
    ).hexdigest()

    # 更新合约
    contract.contract_address = contract_address
    contract.blockchain_tx_id = blockchain_tx_id
    contract.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(contract)

    return {
        "message": "Contract deployed to blockchain successfully",
        "contract_address": contract_address,
        "blockchain_tx_id": blockchain_tx_id,
        "blockchain_network": contract.blockchain_network,
    }