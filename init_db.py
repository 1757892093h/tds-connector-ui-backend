"""
数据库初始化脚本
运行此脚本以创建数据库表并插入初始数据
数据库已包含
4 个数据空间:healthcare, finance, mobility, energy
2 个用户：
Alice (DID: did:example:user123)
Bob (DID: did:example:user456)
2 个连接器：
connector1: Healthcare Provider Connector (属于 Alice)
connector2: Research Institute Connector (属于 Bob)
2 个策略模板（属于 connector1)
1 个合约模板（属于 connector1)
2 个数据资源（属于 connector1)
2 个数据请求
1 个数据合约
"""
import asyncio
from app.database import engine, Base
from app.models import (
    User, DataSpace, Connector, DataOffering, Contract,
    PolicyTemplate, PolicyRule, ContractTemplate, ContractTemplatePolicy,
    DataRequest
)


async def init_database():
    """创建所有数据库表"""
    print("正在创建数据库表...")
    # engine.begin() 是一个上下文管理器，它会自动处理事务。
    # 如果过程出错会回滚，成功则自动提交。
    async with engine.begin() as conn:
        # 删除所有表（谨慎使用）
        await conn.run_sync(Base.metadata.drop_all)

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 数据库表创建成功！")


async def seed_data():
    """插入初始测试数据"""
    from app.database import SessionLocal
    from datetime import datetime, timezone, timedelta

    print("\n正在插入初始数据...")
    async with SessionLocal() as session:
        # 1. 创建数据空间
        print("1. 创建数据空间...")
        data_spaces = [
            DataSpace(
                code="healthcare",
                name="Healthcare Data Space",
                description="Medical and healthcare data sharing"
            ),
            DataSpace(
                code="finance",
                name="Finance Data Space",
                description="Financial data and transactions"
            ),
            DataSpace(
                code="mobility",
                name="Mobility Data Space",
                description="Transportation and logistics data"
            ),
            DataSpace(
                code="energy",
                name="Energy Data Space",
                description="Energy consumption and grid data"
            ),
        ]

        for ds in data_spaces:
            session.add(ds)
        await session.commit()
        for ds in data_spaces:
            await session.refresh(ds)

        print(f"   ✅ 创建了 {len(data_spaces)} 个数据空间")

        # 2. 创建用户
        print("2. 创建测试用户...")
        user1 = User(
            did="did:example:user123",
            username="Alice",
            email="alice@example.com"
        )
        user2 = User(
            did="did:example:user456",
            username="Bob",
            email="bob@example.com"
        )
        session.add(user1)
        session.add(user2)
        await session.commit()
        await session.refresh(user1)
        await session.refresh(user2)

        print(f"   ✅ 创建了 2 个用户: {user1.username}, {user2.username}")

        # 3. 创建连接器
        print("3. 创建连接器...")
        connector1 = Connector(
            did="did:example:connector1",
            display_name="Healthcare Provider Connector",
            status="active",
            did_document={"id": "did:example:connector1", "type": "Connector"},
            owner_user_id=user1.id,
            data_space_id=data_spaces[0].id  # healthcare
        )
        connector2 = Connector(
            did="did:example:connector2",
            display_name="Research Institute Connector",
            status="active",
            did_document={"id": "did:example:connector2", "type": "Connector"},
            owner_user_id=user2.id,
            data_space_id=data_spaces[0].id  # healthcare
        )
        session.add(connector1)
        session.add(connector2)
        await session.commit()
        await session.refresh(connector1)
        await session.refresh(connector2)

        print(f"   ✅ 创建了 2 个连接器")

        # 4. 创建策略模板
        print("4. 创建策略模板...")
        policy_template1 = PolicyTemplate(
            connector_id=connector1.id,
            name="Standard Access Policy",
            description="Standard access control with time and count limits",
            category="access",
            severity="medium",
            enforcement_type="automatic"
        )
        session.add(policy_template1)
        await session.flush()

        # 添加策略规则
        rules1 = [
            PolicyRule(
                policy_template_id=policy_template1.id,
                type="access_period",
                name="30 Day Access Period",
                description="Data access valid for 30 days",
                value="30",
                unit="days",
                is_active=True
            ),
            PolicyRule(
                policy_template_id=policy_template1.id,
                type="access_count",
                name="1000 Access Limit",
                description="Maximum 1000 access requests",
                value="1000",
                unit="requests",
                is_active=True
            )
        ]
        for rule in rules1:
            session.add(rule)

        policy_template2 = PolicyTemplate(
            connector_id=connector1.id,
            name="Premium Access Policy",
            description="Premium access with encryption requirements",
            category="compliance",
            severity="high",
            enforcement_type="hybrid"
        )
        session.add(policy_template2)
        await session.flush()

        rules2 = [
            PolicyRule(
                policy_template_id=policy_template2.id,
                type="encryption",
                name="TLS 1.3 Required",
                description="All data transfers must use TLS 1.3",
                value="TLS1.3",
                unit="protocol",
                is_active=True
            ),
            PolicyRule(
                policy_template_id=policy_template2.id,
                type="ip_restriction",
                name="Whitelist IP Range",
                description="Only allow access from specific IP ranges",
                value="192.168.0.0/16",
                unit="CIDR",
                is_active=True
            )
        ]
        for rule in rules2:
            session.add(rule)

        await session.commit()
        await session.refresh(policy_template1)
        await session.refresh(policy_template2)

        print(f"   ✅ 创建了 2 个策略模板，共 {len(rules1) + len(rules2)} 条规则")

        # 5. 创建合约模板
        print("5. 创建合约模板...")
        contract_template1 = ContractTemplate(
            connector_id=connector1.id,
            name="Standard Data Sharing Agreement",
            description="Standard contract for healthcare data sharing",
            contract_type="multi_policy",
            status="active",
            usage_count=0
        )
        session.add(contract_template1)
        await session.flush()

        # 关联策略模板
        assoc1 = ContractTemplatePolicy(
            contract_template_id=contract_template1.id,
            policy_template_id=policy_template1.id
        )
        assoc2 = ContractTemplatePolicy(
            contract_template_id=contract_template1.id,
            policy_template_id=policy_template2.id
        )
        session.add(assoc1)
        session.add(assoc2)

        await session.commit()
        await session.refresh(contract_template1)

        print(f"   ✅ 创建了 1 个合约模板，关联 2 个策略模板")

        # 6. 创建数据资源
        print("6. 创建数据资源...")
        offering1 = DataOffering(
            connector_id=connector1.id,
            title="Patient Medical Records Dataset",
            description="Anonymized patient medical records for research",
            data_type="s3",
            access_policy="Restricted",
            storage_meta={
                "bucket_name": "healthcare-data",
                "object_key": "medical-records/2024/patients.parquet",
                "region": "us-east-1"
            },
            registration_status="registered"
        )
        offering2 = DataOffering(
            connector_id=connector1.id,
            title="Clinical Trial Results",
            description="Results from recent clinical trials",
            data_type="local_file",
            access_policy="Premium",
            storage_meta={
                "file_path": "/data/clinical_trials_2024.csv",
                "protocol": "local"
            },
            registration_status="registered"
        )
        session.add(offering1)
        session.add(offering2)
        await session.commit()
        await session.refresh(offering1)
        await session.refresh(offering2)

        print(f"   ✅ 创建了 2 个数据资源")

        # 7. 创建数据请求
        print("7. 创建数据请求...")
        request1 = DataRequest(
            data_offering_id=offering1.id,
            consumer_connector_id=connector2.id,
            purpose="Research on patient outcomes and treatment effectiveness",
            access_mode="api",
            status="approved"
        )
        request2 = DataRequest(
            data_offering_id=offering2.id,
            consumer_connector_id=connector2.id,
            purpose="Meta-analysis of clinical trial data",
            access_mode="download",
            status="pending"
        )
        session.add(request1)
        session.add(request2)
        await session.commit()
        await session.refresh(request1)
        await session.refresh(request2)

        print(f"   ✅ 创建了 2 个数据请求")

        # 8. 创建数据合约
        print("8. 创建数据合约...")
        contract1 = Contract(
            name="Medical Research Data Sharing Contract",
            status="active",
            provider_connector_id=connector1.id,
            consumer_connector_id=connector2.id,
            contract_template_id=contract_template1.id,
            data_offering_id=offering1.id,
            data_request_id=request1.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=90)
        )
        session.add(contract1)

        # 更新合约模板使用次数
        contract_template1.usage_count += 1

        await session.commit()
        await session.refresh(contract1)

        print(f"   ✅ 创建了 1 个数据合约")

        print("\n" + "="*60)
        print("数据初始化完成！数据概览：")
        print("="*60)
        print(f"📦 数据空间: {len(data_spaces)}")
        print(f"👥 用户: 2")
        print(f"🔌 连接器: 2")
        print(f"📋 策略模板: 2 (包含 {len(rules1) + len(rules2)} 条规则)")
        print(f"📄 合约模板: 1")
        print(f"💾 数据资源: 2")
        print(f"📨 数据请求: 2")
        print(f"📝 数据合约: 1")
        print("="*60)
        print("\n测试账号信息:")
        print(f"用户1: {user1.username} (DID: {user1.did})")
        print(f"  └─ 连接器: {connector1.display_name}")
        print(f"     └─ 数据空间: {data_spaces[0].name}")
        print(f"\n用户2: {user2.username} (DID: {user2.did})")
        print(f"  └─ 连接器: {connector2.display_name}")
        print(f"     └─ 数据空间: {data_spaces[0].name}")
        print("="*60)


if __name__ == "__main__":
    print("=" * 60)
    print("TDS Connector 数据库初始化")
    print("=" * 60)
    # 因为 Python 脚本默认是同步运行的，不能直接调用 async 函数。
    # asyncio.run() 创建一个事件循环来运行这些异步函数。
    asyncio.run(init_database())
    asyncio.run(seed_data())

    print("\n" + "=" * 60)
    print("✅ 初始化完成！")
    print("=" * 60)
    print("\n下一步：")
    print("1. 启动服务器: uvicorn app.main:app --reload --host 0.0.0.0 --port 8085")
    print("2. 访问 API 文档: http://localhost:8085/docs")
    print("3. 测试完整业务流程：")
    print("   - 查看策略模板: GET /api/v1/policy-templates")
    print("   - 查看合约模板: GET /api/v1/contract-templates")
    print("   - 查看数据请求: GET /api/v1/data-requests")
    print("   - 查看数据合约: GET /api/v1/contracts")
