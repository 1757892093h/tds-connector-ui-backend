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
    from datetime import datetime, timezone

    print("\n正在插入初始数据...")
    async with SessionLocal() as session:
        # 创建测试数据空间
        # 1. 实例化一个模型对象（此时它还只存在于 Python 内存中，未进入数据库）
        data_space = DataSpace(
            code="default-space",
            name="默认数据空间",
            description="用于测试的默认数据空间"
        )
        # 2. 将对象添加到会话中（标记为 Pending 状态）
        session.add(data_space)
        # 3. 提交事务（真正执行 INSERT SQL 语句，保存到数据库）
        await session.commit()
        # 4. 刷新对象（非常重要！）
        # 因为数据库会自动生成 ID（uuid 或 自增主键）和 created_at 时间，
        # commit 后，Python 内存里的 data_space 对象还不知道这些新值。
        # refresh 会重新查询数据库，把这些字段填回对象里。
        await session.refresh(data_space)

        print(f"✅ 创建数据空间: {data_space.name} (ID: {data_space.id})")
        print(f"   - Code: {data_space.code}")
        print(f"\n请使用此 data_space_id 进行测试: {data_space.id}\n")


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
    print("3. 使用上面的 data_space_id 进行测试")
