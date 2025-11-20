from pydantic import BaseModel
from typing import Dict, List, Optional

class DIDGenerateResponse(BaseModel):
    did: str
    didDocument: Dict
    publicKey: str
    privateKey: str

class DIDRegisterRequest(BaseModel):
    did: str
    didDocument: Dict

class RegisterRequest(BaseModel):
    did: str
    didDocument: Dict
    signature: str

class LoginRequest(BaseModel):
    did: str
    signature: str

class AuthResponse(BaseModel):
    token: str
    user: Dict

class DataOffering(BaseModel):
    id: str
    title: str
    description: str
    dataType: str
    accessPolicy: str

class DataOfferingCreate(BaseModel):
    id: str
    title: str
    description: str
    dataType: str
    accessPolicy: str