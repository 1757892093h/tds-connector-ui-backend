"""
数据库初始化脚本
运行此脚本以创建数据库表并插入初始数据
"""
import asyncio
from app.database import engine, Base
from app.models import User, DataSpace, Connector, DataOffering, Contract


async def init_database():
    """创建所有数据库表"""
    print("正在创建数据库表...")
    async with engine.begin() as conn:
        # 删除所有表（谨慎使用）
        # await conn.run_sync(Base.metadata.drop_all)

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 数据库表创建成功！")


async def seed_data():
    """插入初始测试数据"""
    from app.database import SessionLocal
    from datetime import datetime, timezone

    print("\n正在插入初始数据...")

    async with SessionLocal() as session:
        # 创建测试数据空间
        data_space = DataSpace(
            code="default-space",
            name="默认数据空间",
            description="用于测试的默认数据空间"
        )
        session.add(data_space)
        await session.commit()
        await session.refresh(data_space)

        print(f"✅ 创建数据空间: {data_space.name} (ID: {data_space.id})")
        print(f"   - Code: {data_space.code}")
        print(f"\n请使用此 data_space_id 进行测试: {data_space.id}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("TDS Connector 数据库初始化")
    print("=" * 60)

    asyncio.run(init_database())
    asyncio.run(seed_data())

    print("\n" + "=" * 60)
    print("✅ 初始化完成！")
    print("=" * 60)
    print("\n下一步：")
    print("1. 启动服务器: uvicorn app.main:app --reload --host 0.0.0.0 --port 8085")
    print("2. 访问 API 文档: http://localhost:8085/docs")
    print("3. 使用上面的 data_space_id 进行测试")
