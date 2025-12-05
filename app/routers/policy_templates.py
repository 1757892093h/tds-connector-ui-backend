from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_session
from ..deps import get_current_user
from ..models import Connector, PolicyTemplate, PolicyRule
from ..schemas import PolicyTemplateCreate, PolicyTemplateOut

router = APIRouter(prefix=settings.api_prefix + "/policy-templates", tags=["policy-templates"])


@router.post("", response_model=PolicyTemplateOut)
async def create_policy_template(
    payload: PolicyTemplateCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """创建策略模板"""
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

    # 创建策略模板
    policy_template = PolicyTemplate(
        connector_id=payload.connector_id,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        severity=payload.severity,
        enforcement_type=payload.enforcement_type,
    )
    session.add(policy_template)
    await session.flush()  # 获取 policy_template.id

    # 创建策略规则
    for rule_data in payload.rules:
        rule = PolicyRule(
            policy_template_id=policy_template.id,
            type=rule_data.type,
            name=rule_data.name,
            description=rule_data.description,
            value=rule_data.value,
            unit=rule_data.unit,
            is_active=rule_data.is_active,
        )
        session.add(rule)

    await session.commit()
    
    # 重新加载策略模板及其规则，以便正确序列化
    result = await session.execute(
        select(PolicyTemplate)
        .options(selectinload(PolicyTemplate.rules))
        .where(PolicyTemplate.id == policy_template.id)
    )
    policy_template = result.scalar_one_or_none()
    
    return policy_template


@router.get("", response_model=list[PolicyTemplateOut])
async def list_policy_templates(
    connector_id: str | None = None,
    category: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """列出策略模板"""
    # 获取当前用户的所有连接器ID
    user_connectors_result = await session.execute(
        select(Connector.id).where(Connector.owner_user_id == current_user.id)
    )
    user_connector_ids = [row[0] for row in user_connectors_result.fetchall()]

    if not user_connector_ids:
        return []

    # 构建查询，使用 selectinload 加载 rules
    query = select(PolicyTemplate).options(
        selectinload(PolicyTemplate.rules)
    ).where(
        PolicyTemplate.connector_id.in_(user_connector_ids)
    )

    # 过滤条件
    if connector_id:
        if connector_id not in user_connector_ids:
            raise HTTPException(
                status_code=403,
                detail="Connector does not belong to you"
            )
        query = query.where(PolicyTemplate.connector_id == connector_id)

    if category:
        query = query.where(PolicyTemplate.category == category)

    result = await session.execute(query)
    templates = result.scalars().all()
    return templates


@router.get("/{template_id}", response_model=PolicyTemplateOut)
async def get_policy_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """获取策略模板详情"""
    result = await session.execute(
        select(PolicyTemplate)
        .options(selectinload(PolicyTemplate.rules))
        .where(PolicyTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # 验证权限
    result = await session.execute(
        select(Connector).where(Connector.id == template.connector_id)
    )
    connector = result.scalar_one_or_none()
    if not connector or connector.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return template


@router.put("/{template_id}", response_model=PolicyTemplateOut)
async def update_policy_template(
    template_id: str,
    payload: PolicyTemplateCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """更新策略模板"""
    # 查找模板
    result = await session.execute(
        select(PolicyTemplate).where(PolicyTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # 验证权限
    result = await session.execute(
        select(Connector).where(Connector.id == template.connector_id)
    )
    connector = result.scalar_one_or_none()
    if not connector or connector.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 更新基本信息
    template.name = payload.name
    template.description = payload.description
    template.category = payload.category
    template.severity = payload.severity
    template.enforcement_type = payload.enforcement_type
    template.updated_at = datetime.now(timezone.utc)

    # 删除旧规则
    await session.execute(
        select(PolicyRule).where(PolicyRule.policy_template_id == template_id)
    )
    old_rules = (await session.execute(
        select(PolicyRule).where(PolicyRule.policy_template_id == template_id)
    )).scalars().all()
    for rule in old_rules:
        await session.delete(rule)

    # 添加新规则
    for rule_data in payload.rules:
        rule = PolicyRule(
            policy_template_id=template.id,
            type=rule_data.type,
            name=rule_data.name,
            description=rule_data.description,
            value=rule_data.value,
            unit=rule_data.unit,
            is_active=rule_data.is_active,
        )
        session.add(rule)

    await session.commit()
    await session.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_policy_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """删除策略模板"""
    # 查找模板
    result = await session.execute(
        select(PolicyTemplate).where(PolicyTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Policy template not found")

    # 验证权限
    result = await session.execute(
        select(Connector).where(Connector.id == template.connector_id)
    )
    connector = result.scalar_one_or_none()
    if not connector or connector.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 检查是否被合约模板使用
    # TODO: 添加检查逻辑，如果被使用则不允许删除

    await session.delete(template)
    await session.commit()

    return {"message": "Policy template deleted successfully"}
