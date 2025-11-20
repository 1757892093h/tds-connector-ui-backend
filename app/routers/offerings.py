from fastapi import APIRouter, Depends
from typing import List
from ..schemas import DataOffering, DataOfferingCreate
from ..deps import get_current_user

router = APIRouter(prefix="/offerings", tags=["data offerings"])

mock_offerings: List[DataOffering] = []

@router.get("", response_model=List[DataOffering])
async def list_offerings(user=Depends(get_current_user)):
    return mock_offerings

@router.post("", response_model=DataOffering)
async def create_offering(data: DataOfferingCreate, user=Depends(get_current_user)):
    offering = DataOffering(**data.dict())
    mock_offerings.append(offering)
    return offering