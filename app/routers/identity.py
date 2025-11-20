from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import DIDGenerateResponse, DIDRegisterRequest
from ..services.did_service import DIDService
from ..database import get_session

router = APIRouter(prefix="/identity", tags=["identity"])

@router.post("/did/generate", response_model=DIDGenerateResponse)
async def generate_did():
    return DIDService.generate_did()

@router.post("/did/register")
async def register_did(request: DIDRegisterRequest, session: AsyncSession = Depends(get_session)):
    success = await DIDService.register_did(session, request.did, request.didDocument)
    if not success:
        raise HTTPException(status_code=400, detail="DID already registered")
    return {"status": "success", "did": request.did}

@router.get("/did/{did}")
async def get_did(did: str, session: AsyncSession = Depends(get_session)):
    record = await DIDService.get_did(session, did)
    if not record:
        raise HTTPException(status_code=404, detail="DID not found")
    return {"did": record.did, "didDocument": record.document}