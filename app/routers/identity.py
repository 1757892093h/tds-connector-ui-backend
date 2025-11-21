from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_session
from ..deps import get_current_user
from ..models import Connector, DataSpace
from ..schemas import ConnectorCreate, ConnectorOut
from ..services.did_service import DIDService

router = APIRouter(prefix=settings.api_prefix + "/identity", tags=["identity"])


@router.post("/did/generate")
async def generate_did():
    return DIDService.generate_did()


@router.post("/did/register", response_model=ConnectorOut)
async def register_connector(
    payload: ConnectorCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    result = await session.execute(select(DataSpace).where(DataSpace.id == payload.data_space_id))
    data_space = result.scalar_one_or_none()
    if not data_space:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data space not found")

    connector = Connector(
        did=payload.did,
        display_name=payload.display_name,
        data_space_id=data_space.id,
        owner_user_id=current_user.id,
        did_document=payload.did_document,
        status="registered",
    )
    session.add(connector)
    await session.commit()
    await session.refresh(connector)
    return connector


@router.get("/connectors", response_model=list[ConnectorOut])
async def list_connectors(
    data_space_id: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    query = select(Connector).where(Connector.owner_user_id == current_user.id)
    if data_space_id:
        query = query.where(Connector.data_space_id == data_space_id)
    result = await session.execute(query)
    connectors = result.scalars().all()
    return connectors