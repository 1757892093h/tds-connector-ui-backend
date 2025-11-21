"""
API 测试脚本
使用 httpx 库测试所有 API 端点
运行: python test_api.py
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8085"
API_PREFIX = "/api/v1"

# 全局变量存储测试数据
test_data = {
    "did_info": None,
    "token": None,
    "user_id": None,
    "data_space_id": None,  # 需要从数据库获取
    "connector_id": None,
    "offering_id": None,
    "contract_id": None,
}


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_test(title: str):
    """打印测试标题"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_info(message: str):
    """打印信息"""
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.RESET}")


async def test_1_generate_did():
    """测试 1: 生成 DID"""
    print_test("测试 1: 生成 DID")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}{API_PREFIX}/identity/did/generate")

        if response.status_code == 200:
            data = response.json()
            test_data["did_info"] = data
            print_success(f"DID 生成成功")
            print(f"   DID: {data['did']}")
            print(f"   Public Key: {data['publicKey'][:20]}...")
            print(f"   Private Key: {data['privateKey'][:20]}...")
            return True
        else:
            print_error(f"生成失败: {response.status_code} - {response.text}")
            return False


async def test_2_register_user():
    """测试 2: 注册用户"""
    print_test("测试 2: 注册用户")

    if not test_data["did_info"]:
        print_error("请先生成 DID")
        return False

    payload = {
        "did": test_data["did_info"]["did"],
        "signature": "demo-signature-12345",  # Demo 签名
        "username": "测试用户",
        "email": "test@example.com"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json=payload
        )

        if response.status_code == 201:
            data = response.json()
            test_data["token"] = data["token"]
            test_data["user_id"] = data["user"]["id"]
            print_success(f"用户注册成功")
            print(f"   User ID: {data['user']['id']}")
            print(f"   Username: {data['user']['username']}")
            print(f"   Token: {data['token'][:30]}...")
            return True
        else:
            print_error(f"注册失败: {response.status_code} - {response.text}")
            return False


async def test_3_login_user():
    """测试 3: 用户登录"""
    print_test("测试 3: 用户登录")

    if not test_data["did_info"]:
        print_error("请先生成 DID 并注册")
        return False

    payload = {
        "did": test_data["did_info"]["did"],
        "signature": "demo-signature-12345"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            test_data["token"] = data["token"]  # 更新 token
            print_success(f"用户登录成功")
            print(f"   User ID: {data['user']['id']}")
            print(f"   New Token: {data['token'][:30]}...")
            return True
        else:
            print_error(f"登录失败: {response.status_code} - {response.text}")
            return False


async def test_4_verify_token():
    """测试 4: 验证 Token"""
    print_test("测试 4: 验证 Token")

    if not test_data["token"]:
        print_error("请先登录获取 Token")
        return False

    headers = {"Authorization": f"Bearer {test_data['token']}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/auth/verify",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Token 验证成功")
            print(f"   User DID: {data['did']}")
            return True
        else:
            print_error(f"验证失败: {response.status_code} - {response.text}")
            return False


async def test_5_register_connector():
    """测试 5: 注册连接器"""
    print_test("测试 5: 注册连接器")

    if not test_data["token"]:
        print_error("请先登录获取 Token")
        return False

    # 获取 data_space_id
    print_info("请输入 data_space_id (从 init_db.py 输出中获取):")
    test_data["data_space_id"] = input("   > ").strip()

    if not test_data["data_space_id"]:
        print_error("data_space_id 不能为空")
        return False

    # 生成新的 DID 作为连接器 DID
    async with httpx.AsyncClient() as client:
        did_response = await client.post(f"{BASE_URL}{API_PREFIX}/identity/did/generate")
        connector_did_info = did_response.json()

    payload = {
        "did": connector_did_info["did"],
        "display_name": "测试数据连接器",
        "data_space_id": test_data["data_space_id"],
        "did_document": connector_did_info["didDocument"]
    }

    headers = {"Authorization": f"Bearer {test_data['token']}"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/identity/did/register",
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            test_data["connector_id"] = data["id"]
            print_success(f"连接器注册成功")
            print(f"   Connector ID: {data['id']}")
            print(f"   Connector DID: {data['did']}")
            print(f"   Display Name: {data['display_name']}")
            print(f"   Status: {data['status']}")
            return True
        else:
            print_error(f"注册失败: {response.status_code} - {response.text}")
            return False


async def test_6_list_connectors():
    """测试 6: 列出连接器"""
    print_test("测试 6: 列出用户的连接器")

    if not test_data["token"]:
        print_error("请先登录获取 Token")
        return False

    headers = {"Authorization": f"Bearer {test_data['token']}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/identity/connectors",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"获取连接器列表成功")
            print(f"   总数: {len(data)} 个连接器")
            for conn in data:
                print(f"   - {conn['display_name']} ({conn['did']})")
            return True
        else:
            print_error(f"获取失败: {response.status_code} - {response.text}")
            return False


async def test_7_create_offering():
    """测试 7: 创建数据产品"""
    print_test("测试 7: 创建数据产品")

    if not test_data["token"] or not test_data["connector_id"]:
        print_error("请先注册连接器")
        return False

    storage_meta = {
        "file_path": "/data/test.csv",
        "protocol": "local"
    }

    form_data = {
        "connector_id": test_data["connector_id"],
        "title": "测试数据集",
        "description": "这是一个测试数据集，包含示例数据",
        "data_type": "local_file",
        "access_policy": "Open",
        "storage_meta": json.dumps(storage_meta)
    }

    headers = {"Authorization": f"Bearer {test_data['token']}"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/offerings",
            data=form_data,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            test_data["offering_id"] = data["id"]
            print_success(f"数据产品创建成功")
            print(f"   Offering ID: {data['id']}")
            print(f"   Title: {data['title']}")
            print(f"   Data Type: {data['data_type']}")
            print(f"   Access Policy: {data['access_policy']}")
            return True
        else:
            print_error(f"创建失败: {response.status_code} - {response.text}")
            return False


async def test_8_list_offerings():
    """测试 8: 列出数据产品"""
    print_test("测试 8: 列出数据产品")

    if not test_data["token"]:
        print_error("请先登录获取 Token")
        return False

    headers = {"Authorization": f"Bearer {test_data['token']}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/offerings",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"获取数据产品列表成功")
            print(f"   总数: {len(data)} 个产品")
            for offering in data:
                print(f"   - {offering['title']} ({offering['data_type']})")
            return True
        else:
            print_error(f"获取失败: {response.status_code} - {response.text}")
            return False


async def test_9_create_contract():
    """测试 9: 创建合约"""
    print_test("测试 9: 创建合约")

    if not test_data["token"] or not test_data["connector_id"]:
        print_error("请先注册连接器")
        return False

    # 注册第二个连接器作为消费者
    async with httpx.AsyncClient() as client:
        did_response = await client.post(f"{BASE_URL}{API_PREFIX}/identity/did/generate")
        consumer_did_info = did_response.json()

    consumer_payload = {
        "did": consumer_did_info["did"],
        "display_name": "消费者连接器",
        "data_space_id": test_data["data_space_id"],
        "did_document": consumer_did_info["didDocument"]
    }

    headers = {"Authorization": f"Bearer {test_data['token']}"}

    async with httpx.AsyncClient() as client:
        consumer_response = await client.post(
            f"{BASE_URL}{API_PREFIX}/identity/did/register",
            json=consumer_payload,
            headers=headers
        )
        consumer_connector = consumer_response.json()
        consumer_connector_id = consumer_connector["id"]

    # 创建合约
    contract_payload = {
        "name": "数据共享合约",
        "policy": "按次付费",
        "provider_connector_id": test_data["connector_id"],
        "consumer_connector_id": consumer_connector_id,
        "status": "active"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/contracts",
            json=contract_payload,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            test_data["contract_id"] = data["id"]
            print_success(f"合约创建成功")
            print(f"   Contract ID: {data['id']}")
            print(f"   Name: {data['name']}")
            print(f"   Policy: {data['policy']}")
            print(f"   Status: {data['status']}")
            return True
        else:
            print_error(f"创建失败: {response.status_code} - {response.text}")
            return False


async def test_10_list_contracts():
    """测试 10: 列出合约"""
    print_test("测试 10: 列出合约")

    if not test_data["token"]:
        print_error("请先登录获取 Token")
        return False

    headers = {"Authorization": f"Bearer {test_data['token']}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/contracts",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"获取合约列表成功")
            print(f"   总数: {len(data)} 个合约")
            for contract in data:
                print(f"   - {contract['name']} ({contract['policy']}) - {contract['status']}")
            return True
        else:
            print_error(f"获取失败: {response.status_code} - {response.text}")
            return False


async def main():
    """主测试流程"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("TDS Connector API 测试套件")
    print(f"{'='*60}{Colors.RESET}\n")

    print_info(f"API 地址: {BASE_URL}{API_PREFIX}")
    print_info("请确保服务器正在运行: uvicorn app.main:app --reload --port 8085\n")

    # 检查服务器是否运行
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/", timeout=5.0)
            if response.status_code == 200:
                print_success("服务器连接成功！\n")
            else:
                print_error("服务器响应异常")
                return
    except Exception as e:
        print_error(f"无法连接到服务器: {e}")
        print_info("请先启动服务器: uvicorn app.main:app --reload --port 8085")
        return

    # 运行所有测试
    tests = [
        test_1_generate_did,
        test_2_register_user,
        test_3_login_user,
        test_4_verify_token,
        test_5_register_connector,
        test_6_list_connectors,
        test_7_create_offering,
        test_8_list_offerings,
        test_9_create_contract,
        test_10_list_contracts,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
            if not result:
                print_info("测试失败，是否继续？(y/n)")
                choice = input("   > ").strip().lower()
                if choice != 'y':
                    break
        except Exception as e:
            print_error(f"测试异常: {e}")
            results.append(False)
            break

    # 总结
    print(f"\n{Colors.BLUE}{'='*60}")
    print("测试总结")
    print(f"{'='*60}{Colors.RESET}")
    passed = sum(results)
    total = len(results)
    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print_success("所有测试通过！🎉")
    else:
        print_error(f"有 {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
