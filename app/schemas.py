from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


  # -------- User / Auth --------
class RegisterRequest(BaseModel):
    """用户注册请求"""
    did: str
    signature: str
    username: str | None = None
    email: str | None = None


class LoginRequest(BaseModel):
    """用户登录请求"""
    did: str
    signature: str


class UserCreate(BaseModel):
    did: str
    did_document: dict
    signature: str
    username: str | None = None
    email: str | None = None


class UserOut(BaseModel):
    id: str
    did: str
    username: str | None = None
    email: str | None = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class AuthResponse(BaseModel):
    """认证响应（注册/登录）"""
    token: str
    user: UserOut


class TokenVerifyResponse(BaseModel):
    id: str
    did: str
    username: str | None = None
    email: str | None = None

    class Config:
        from_attributes = True


  # -------- Connector --------
class ConnectorBase(BaseModel):
    did: str
    display_name: str
    data_space_id: str
    did_document: dict


class ConnectorCreate(ConnectorBase):
    pass


class ConnectorOut(BaseModel):
    id: str
    did: str
    display_name: str
    status: str
    data_space_id: str
    created_at: datetime

    class Config:
        from_attributes = True


  # -------- DataSpace --------
class DataSpaceOut(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


  # -------- Data Offering --------
class StorageMeta(BaseModel):
    bucket_name: str | None = None
    object_key: str | None = None
    region: str | None = None
    file_path: str | None = None
    protocol: str | None = None
    api_endpoint: str | None = None
    extras: dict | None = None


class DataOfferingCreate(BaseModel):
    connector_id: str
    title: str
    description: str
    data_type: Literal["local_file", "s3", "nas", "restful"]
    access_policy: Literal["Open", "Restricted", "Premium"]
    storage_meta: StorageMeta
    registration_status: str | None = None


class DataOfferingOut(BaseModel):
    id: str
    connector_id: str
    title: str
    description: str
    data_type: str
    access_policy: str
    storage_meta: dict
    registration_status: str
    created_at: datetime

    class Config:
        from_attributes = True


  # -------- Contract --------
class ContractCreate(BaseModel):
    name: str
    policy: str
    provider_connector_id: str
    consumer_connector_id: str
    contract_address: str | None = None
    status: str | None = None
    expires_at: datetime | None = None


class ContractOut(BaseModel):
    id: str
    name: str
    policy: str
    status: str
    provider_connector_id: str
    consumer_connector_id: str
    contract_address: str | None
    expires_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True 