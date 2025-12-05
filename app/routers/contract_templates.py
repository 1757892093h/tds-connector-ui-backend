from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_session
from ..deps import get_current_user
from ..models import Connector, ContractTemplate, PolicyTemplate, ContractTemplatePolicy
from ..schemas import ContractTemplateCreate, ContractTemplateOut

router = APIRouter(prefix=settings.api_prefix + "/contract-templates", tags=["contract-templates"])


@router.post("", response_model=ContractTemplateOut)
async def create_contract_template(
    payload: ContractTemplateCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """创建合约模板"""
    # 验证连接器属于当前用户
    result = await session.execute(
        select(Connector).where(Connector.id == payload.connector_id)
    )
    connector = result.scalar_one_or_none()
    if not connector or connector.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Connector not found or not owned by you"
        )

    # 验证策略模板
    if not payload.policy_template_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one policy template is required"
        )

    # 验证单策略模板类型
    if payload.contract_type == "single_policy" and len(payload.policy_template_ids) > 1:
        raise HTTPException(
            status_code=400,
            detail="Single policy contract can only have one policy template"
        )

    # 验证所有策略模板存在且属于当前用户
    policy_templates = []
    for policy_id in payload.policy_template_ids:
        result = await session.execute(
            select(PolicyTemplate).where(PolicyTemplate.id == policy_id)
        )
        policy_template = result.scalar_one_or_none()

        if not policy_template:
            raise HTTPException(
                status_code=404,
                detail=f"Policy template {policy_id} not found"
            )

        # 验证策略模板的连接器属于当前用户
        result = await session.execute(
            select(Connector).where(Connector.id == policy_template.connector_id)
        )
        policy_connector = result.scalar_one_or_none()
        if not policy_connector or policy_connector.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail=f"Policy template {policy_id} does not belong to you"
            )

        policy_templates.append(policy_template)

    # 创建合约模板
    contract_template = ContractTemplate(
        connector_id=payload.connector_id,
        name=payload.name,
        description=payload.description,
        contract_type=payload.contract_type,
        status=payload.status,
        usage_count=0,
    )
    session.add(contract_template)
    await session.flush()  # 获取 contract_template.id

    # 创建关联关系
    for policy_template in policy_templates:
        association = ContractTemplatePolicy(
            contract_template_id=contract_template.id,
            policy_template_id=policy_template.id,
        )
        session.add(association)

    await session.commit()
    await session.refresh(contract_template)
    return contract_template


@router.get("", response_model=list[ContractTemplateOut])
async def list_contract_templates(
    connector_id: str | None = None,
    contract_type: str | None = None,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """列出合约模板"""
    # 获取当前用户的所有连接器ID
    user_connectors_result = await session.execute(
        select(Connector.id).where(Connector.owner_user_id == current_user.id)
    )
    user_connector_ids = [row[0] for row in user_connectors_result.fetchall()]

    if not user_connector_ids:
        return []

    # 构建查询，使用 selectinload 加载 policy_templates 和它们的 rules
    query = select(ContractTemplate).options(
        selectinload(ContractTemplate.policy_templates).selectinload(PolicyTemplate.rules)
    ).where(
        ContractTemplate.connector_id.in_(user_connector_ids)
    )

    # 过滤条件
    if connector_id:
        if connector_id not in user_connector_ids:
            raise HTTPException(
                status_code=403,
                detail="Connector does not belong to you"
            )
        query = query.where(ContractTemplate.connector_id == connector_id)

    if contract_type:
        query = query.where(ContractTemplate.contract_type == contract_type)

    if status:
        query = query.where(ContractTemplate.status == status)

    result = await session.execute(query)
    templates = result.scalars().all()
    return templates


@router.get("/{template_id}", response_model=ContractTemplateOut)
async def get_contract_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """获取合约模板详情"""
    result = await session.execute(
        select(ContractTemplate)
        .options(
            selectinload(ContractTemplate.policy_templates).selectinload(PolicyTemplate.rules)
        )
        .where(ContractTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Contract template not found")

    # 验证权限
    result = await session.execute(
        select(Connector).where(Connector.id == template.connector_id)
    )
    connector = result.scalar_one_or_none()
    if not connector or connector.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return template


@router.put("/{template_id}", response_model=ContractTemplateOut)
async def update_contract_template(
    template_id: str,
    payload: ContractTemplateCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """更新合约模板"""
    # 查找模板
    result = await session.execute(
        select(ContractTemplate).where(ContractTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Contract template not found")

    # 验证权限
    result = await session.execute(
        select(Connector).where(Connector.id == template.connector_id)
    )
    connector = result.scalar_one_or_none()
    if not connector or connector.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 验证策略模板
    if not payload.policy_template_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one policy template is required"
        )

    # 验证单策略模板类型
    if payload.contract_type == "single_policy" and len(payload.policy_template_ids) > 1:
        raise HTTPException(
            status_code=400,
            detail="Single policy contract can only have one policy template"
        )

    # 验证所有策略模板存在且属于当前用户
    policy_templates = []
    for policy_id in payload.policy_template_ids:
        result = await session.execute(
            select(PolicyTemplate).where(PolicyTemplate.id == policy_id)
        )
        policy_template = result.scalar_one_or_none()

        if not policy_template:
            raise HTTPException(
                status_code=404,
                detail=f"Policy template {policy_id} not found"
            )

        # 验证策略模板的连接器属于当前用户
        result = await session.execute(
            select(Connector).where(Connector.id == policy_template.connector_id)
        )
        policy_connector = result.scalar_one_or_none()
        if not policy_connector or policy_connector.owner_user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail=f"Policy template {policy_id} does not belong to you"
            )

        policy_templates.append(policy_template)

    # 更新基本信息
    template.name = payload.name
    template.description = payload.description
    template.contract_type = payload.contract_type
    template.status = payload.status
    template.updated_at = datetime.now(timezone.utc)

    # 删除旧关联
    old_associations = (await session.execute(
        select(ContractTemplatePolicy).where(
            ContractTemplatePolicy.contract_template_id == template_id
        )
    )).scalars().all()
    for assoc in old_associations:
        await session.delete(assoc)

    # 添加新关联
    for policy_template in policy_templates:
        association = ContractTemplatePolicy(
            contract_template_id=template.id,
            policy_template_id=policy_template.id,
        )
        session.add(association)

    await session.commit()
    await session.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_contract_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """删除合约模板"""
    # 查找模板
    result = await session.execute(
        select(ContractTemplate).where(ContractTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Contract template not found")

    # 验证权限
    result = await session.execute(
        select(Connector).where(Connector.id == template.connector_id)
    )
    connector = result.scalar_one_or_none()
    if not connector or connector.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 检查是否被合约使用
    # TODO: 添加检查逻辑，如果被使用则不允许删除

    await session.delete(template)
    await session.commit()

    return {"message": "Contract template deleted successfully"}
