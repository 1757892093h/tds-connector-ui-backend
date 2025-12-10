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
    did_document: dict
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


class DataOfferingWithCountsOut(BaseModel):
    """数据资源列表项，包含策略模板和合约模板数量"""
    id: str
    connector_id: str
    title: str
    description: str
    data_type: str
    access_policy: str
    storage_meta: dict
    registration_status: str
    created_at: datetime
    # 提供者连接器的策略模板数量
    policy_templates_count: int = 0
    # 提供者连接器的合约模板数量
    contract_templates_count: int = 0

    class Config:
        from_attributes = True


  # -------- Policy Rule --------
class PolicyRuleCreate(BaseModel):
    type: Literal[
        "access_period", "access_count", "identity_restriction",
        "encryption", "ip_restriction", "transfer_limit", "qps_limit"
    ]
    name: str
    description: str
    value: str
    unit: str | None = None
    is_active: bool = True


class PolicyRuleOut(BaseModel):
    id: str
    type: str
    name: str
    description: str
    value: str
    unit: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


  # -------- Policy Template --------
class PolicyTemplateCreate(BaseModel):
    connector_id: str
    name: str
    description: str
    category: Literal["access", "usage", "retention", "compliance"]
    severity: Literal["low", "medium", "high"]
    enforcement_type: Literal["automatic", "manual", "hybrid"]
    rules: list[PolicyRuleCreate]


class PolicyTemplateOut(BaseModel):
    id: str
    connector_id: str
    name: str
    description: str
    category: str
    severity: str
    enforcement_type: str
    created_at: datetime
    updated_at: datetime | None
    rules: list[PolicyRuleOut]

    class Config:
        from_attributes = True


  # -------- Contract Template --------
class ContractTemplateCreate(BaseModel):
    connector_id: str
    name: str
    description: str
    contract_type: Literal["single_policy", "multi_policy"]
    policy_template_ids: list[str]
    status: Literal["draft", "active"] = "draft"


class ContractTemplateOut(BaseModel):
    id: str
    connector_id: str
    name: str
    description: str
    contract_type: str
    status: str
    usage_count: int
    created_at: datetime
    updated_at: datetime | None
    policy_templates: list[PolicyTemplateOut]

    class Config:
        from_attributes = True


class DataOfferingDetailOut(BaseModel):
    """数据资源详情，包含策略模板和合约模板信息"""
    id: str
    connector_id: str
    title: str
    description: str
    data_type: str
    access_policy: str
    storage_meta: dict
    registration_status: str
    created_at: datetime
    # 提供者连接器的策略模板列表
    policy_templates: list[PolicyTemplateOut] = []
    # 提供者连接器的合约模板列表
    contract_templates: list[ContractTemplateOut] = []

    class Config:
        from_attributes = True


  # -------- Data Request --------
class DataRequestCreate(BaseModel):
    data_offering_id: str
    consumer_connector_id: str
    purpose: str
    access_mode: Literal["api", "download"]


class DataRequestUpdate(BaseModel):
    status: Literal["pending", "approved", "rejected", "completed"]


class DataRequestOut(BaseModel):
    id: str
    data_offering_id: str
    consumer_connector_id: str
    purpose: str
    access_mode: str
    status: str
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


  # -------- Contract --------
class ContractCreate(BaseModel):
    name: str
    provider_connector_id: str
    consumer_connector_id: str
    contract_template_id: str
    data_offering_id: str
    data_request_id: str | None = None
    expires_at: datetime | None = None


class ContractConfirm(BaseModel):
    """消费者确认合约"""
    action: Literal["confirm", "reject"]


class ContractOut(BaseModel):
    id: str
    name: str
    status: str
    provider_connector_id: str
    consumer_connector_id: str
    contract_template_id: str
    data_offering_id: str
    data_request_id: str | None
    contract_address: str | None
    blockchain_tx_id: str | None
    blockchain_network: str
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True