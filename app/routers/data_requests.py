from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_session
from ..deps import get_current_user
from ..models import Connector, DataOffering, DataRequest
from ..schemas import DataRequestCreate, DataRequestUpdate, DataRequestOut

router = APIRouter(prefix=settings.api_prefix + "/data-requests", tags=["data-requests"])


@router.post("", response_model=DataRequestOut)
async def create_data_request(
    payload: DataRequestCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """创建数据访问请求（消费者发起）"""
    # 验证消费者连接器属于当前用户
    result = await session.execute(
        select(Connector).where(Connector.id == payload.consumer_connector_id)
    )
    consumer_connector = result.scalar_one_or_none()
    if not consumer_connector or consumer_connector.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Consumer connector not found or not owned by you"
        )

    # 验证数据资源存在
    result = await session.execute(
        select(DataOffering).where(DataOffering.id == payload.data_offering_id)
    )
    data_offering = result.scalar_one_or_none()
    if not data_offering:
        raise HTTPException(
            status_code=404,
            detail="Data offering not found"
        )

    # 验证不是自己的数据资源
    if data_offering.connector_id == payload.consumer_connector_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot request your own data offering"
        )

    # 创建请求
    data_request = DataRequest(
        data_offering_id=payload.data_offering_id,
        consumer_connector_id=payload.consumer_connector_id,
        purpose=payload.purpose,
        access_mode=payload.access_mode,
        status="pending",
    )
    session.add(data_request)
    await session.commit()
    await session.refresh(data_request)
    return data_request


@router.get("", response_model=list[DataRequestOut])
async def list_data_requests(
    connector_id: str | None = None,
    role: str | None = None,  # "consumer" or "provider"
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    列出数据请求
    - role=consumer: 作为消费者发起的请求
    - role=provider: 作为提供者收到的请求
    - 不指定role: 所有相关请求
    """
    # 获取当前用户的所有连接器ID
    user_connectors_result = await session.execute(
        select(Connector.id).where(Connector.owner_user_id == current_user.id)
    )
    user_connector_ids = [row[0] for row in user_connectors_result.fetchall()]

    if not user_connector_ids:
        return []

    # 如果指定了connector_id，验证权限
    if connector_id and connector_id not in user_connector_ids:
        raise HTTPException(
            status_code=403,
            detail="Connector does not belong to you"
        )

    # 构建查询
    if role == "consumer":
        # 作为消费者：查看自己发起的请求
        if connector_id:
            query = select(DataRequest).where(
                DataRequest.consumer_connector_id == connector_id
            )
        else:
            query = select(DataRequest).where(
                DataRequest.consumer_connector_id.in_(user_connector_ids)
            )
    elif role == "provider":
        # 作为提供者：查看针对自己数据资源的请求
        # 先获取当前用户的所有数据资源
        offerings_result = await session.execute(
            select(DataOffering.id).where(
                DataOffering.connector_id.in_(user_connector_ids)
            )
        )
        offering_ids = [row[0] for row in offerings_result.fetchall()]

        if not offering_ids:
            return []

        if connector_id:
            # 过滤该连接器的数据资源
            offerings_result = await session.execute(
                select(DataOffering.id).where(
                    DataOffering.connector_id == connector_id
                )
            )
            offering_ids = [row[0] for row in offerings_result.fetchall()]

        query = select(DataRequest).where(
            DataRequest.data_offering_id.in_(offering_ids)
        )
    else:
        # 所有相关请求
        # 获取作为消费者的请求
        consumer_requests_ids = []
        # 获取作为提供者的请求（通过数据资源）
        offerings_result = await session.execute(
            select(DataOffering.id).where(
                DataOffering.connector_id.in_(user_connector_ids)
            )
        )
        offering_ids = [row[0] for row in offerings_result.fetchall()]

        if connector_id:
            query = select(DataRequest).where(
                or_(
                    DataRequest.consumer_connector_id == connector_id,
                    DataRequest.data_offering_id.in_(offering_ids)
                )
            )
        else:
            query = select(DataRequest).where(
                or_(
                    DataRequest.consumer_connector_id.in_(user_connector_ids),
                    DataRequest.data_offering_id.in_(offering_ids)
                )
            )

    # 状态过滤
    if status:
        query = query.where(DataRequest.status == status)

    result = await session.execute(query)
    requests = result.scalars().all()
    return requests


@router.get("/{request_id}", response_model=DataRequestOut)
async def get_data_request(
    request_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """获取数据请求详情"""
    result = await session.execute(
        select(DataRequest)
        .options(
            selectinload(DataRequest.data_offering).selectinload(DataOffering.connector)
        )
        .where(DataRequest.id == request_id)
    )
    data_request = result.scalar_one_or_none()

    if not data_request:
        raise HTTPException(status_code=404, detail="Data request not found")

    # 验证权限：是消费者或是提供者
    result = await session.execute(
        select(Connector).where(Connector.id == data_request.consumer_connector_id)
    )
    consumer_connector = result.scalar_one_or_none()

    is_consumer = consumer_connector and consumer_connector.owner_user_id == current_user.id
    is_provider = data_request.data_offering.connector.owner_user_id == current_user.id

    if not (is_consumer or is_provider):
        raise HTTPException(status_code=403, detail="Access denied")

    return data_request


@router.put("/{request_id}/approve", response_model=DataRequestOut)
async def approve_data_request(
    request_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """同意数据请求（提供者）"""
    result = await session.execute(
        select(DataRequest).where(DataRequest.id == request_id)
    )
    data_request = result.scalar_one_or_none()

    if not data_request:
        raise HTTPException(status_code=404, detail="Data request not found")

    # 验证是提供者
    result = await session.execute(
        select(DataOffering).where(DataOffering.id == data_request.data_offering_id)
    )
    data_offering = result.scalar_one_or_none()

    if not data_offering:
        raise HTTPException(status_code=404, detail="Data offering not found")

    result = await session.execute(
        select(Connector).where(Connector.id == data_offering.connector_id)
    )
    provider_connector = result.scalar_one_or_none()

    if not provider_connector or provider_connector.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the data provider can approve this request"
        )

    # 检查状态
    if data_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve request with status: {data_request.status}"
        )

    # 更新状态
    data_request.status = "approved"
    data_request.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(data_request)
    return data_request


@router.put("/{request_id}/reject", response_model=DataRequestOut)
async def reject_data_request(
    request_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """拒绝数据请求（提供者）"""
    result = await session.execute(
        select(DataRequest).where(DataRequest.id == request_id)
    )
    data_request = result.scalar_one_or_none()

    if not data_request:
        raise HTTPException(status_code=404, detail="Data request not found")

    # 验证是提供者
    result = await session.execute(
        select(DataOffering).where(DataOffering.id == data_request.data_offering_id)
    )
    data_offering = result.scalar_one_or_none()

    if not data_offering:
        raise HTTPException(status_code=404, detail="Data offering not found")

    result = await session.execute(
        select(Connector).where(Connector.id == data_offering.connector_id)
    )
    provider_connector = result.scalar_one_or_none()

    if not provider_connector or provider_connector.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the data provider can reject this request"
        )

    # 检查状态
    if data_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject request with status: {data_request.status}"
        )

    # 更新状态
    data_request.status = "rejected"
    data_request.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(data_request)
    return data_request
