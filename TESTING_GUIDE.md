# TDS Connector API 测试指南

## 📋 目录
1. [代码检查结果](#代码检查结果)
2. [环境准备](#环境准备)
3. [安装依赖](#安装依赖)
4. [初始化数据库](#初始化数据库)
5. [启动服务器](#启动服务器)
6. [测试方法](#测试方法)
7. [API 端点说明](#api-端点说明)
8. [故障排查](#故障排查)

---

## ✅ 代码检查结果

### 已修复的错误：

1. **schemas.py** - ✅ 添加了缺失的类定义
   - `RegisterRequest`
   - `LoginRequest`
   - `AuthResponse`

2. **deps.py** - ✅ 添加了 JWT 异常处理
   - `jwt.ExpiredSignatureError` - Token 过期处理
   - `jwt.InvalidTokenError` - Token 无效处理

3. **models.py** - ✅ 修复了已弃用的 `datetime.utcnow()`
   - 改用 `datetime.now(timezone.utc)`

4. **offerings.py** - ✅ 添加了缺失的 `json` 模块导入

5. **contracts.py** - ✅ 修复了权限验证逻辑
   - 改进了查询逻辑，确保用户只能看到自己的合约

6. **requirements.txt** - ✅ 添加了缺失的依赖
   - `passlib[bcrypt]==1.7.4` - 密码哈希库
   - `python-multipart==0.0.9` - 文件上传支持

### ⚠️ 已知限制（仅用于 Demo）：

1. **security.py:24-26** - `verify_signature()` 未实现真实签名验证
   ```python
   # 当前实现：任何非空签名都通过
   def verify_signature(did: str, signature: str, message: str) -> bool:
       return bool(signature)
   ```
   **生产环境必须实现真实的公钥验签！**

---

## 🛠️ 环境准备

### 1. Python 版本
- **要求**: Python 3.11 或 3.12
- **检查版本**:
  ```bash
  python --version
  ```

### 2. 推荐使用虚拟环境
```bash
# 创建虚拟环境
conda create -n tds-backend python=3.12
conda activate tds-backend

# 或使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

---

## 📦 安装依赖

```bash
# 进入项目目录
cd D:\wjh\tds-connector-ui-backend

# 安装所有依赖
pip install -r requirements.txt
```

### 依赖列表说明：
| 包名 | 版本 | 用途 |
|------|------|------|
| fastapi | 0.111.0 | Web 框架 |
| uvicorn[standard] | 0.30.1 | ASGI 服务器 |
| pydantic | 2.8.2 | 数据验证 |
| SQLAlchemy | 2.0.32 | ORM 框架 |
| aiosqlite | 0.20.0 | 异步 SQLite 驱动 |
| pyjwt | 2.9.0 | JWT Token |
| passlib[bcrypt] | 1.7.4 | 密码哈希 |
| python-multipart | 0.0.9 | 文件上传 |

---

## 🗄️ 初始化数据库

### 方法一：使用初始化脚本（推荐）

```bash
python init_db.py
```

**输出示例：**
```
============================================================
TDS Connector 数据库初始化
============================================================
正在创建数据库表...
✅ 数据库表创建成功！

正在插入初始数据...
✅ 创建数据空间: 默认数据空间 (ID: abc-123-def)
   - Code: default-space

请使用此 data_space_id 进行测试: abc-123-def

============================================================
✅ 初始化完成！
============================================================
```

**⚠️ 重要：保存输出的 `data_space_id`，后续测试需要使用！**

### 方法二：手动创建数据库

创建文件 `create_tables.py`:
```python
import asyncio
from app.database import engine, Base

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表创建成功！")

asyncio.run(create_tables())
```

然后运行：
```bash
python create_tables.py
```

---

## 🚀 启动服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8085
```

**参数说明：**
- `--reload` - 代码修改后自动重启（开发模式）
- `--host 0.0.0.0` - 监听所有网络接口
- `--port 8085` - 端口号

**成功启动输出：**
```
INFO:     Uvicorn running on http://0.0.0.0:8085 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**访问：**
- API 文档: http://localhost:8085/docs
- ReDoc 文档: http://localhost:8085/redoc
- OpenAPI JSON: http://localhost:8085/openapi.json

---

## 🧪 测试方法

### 方法一：自动化测试脚本（推荐）

```bash
# 安装测试依赖
pip install httpx

# 运行测试
python test_api.py
```

**测试流程：**
1. ✅ 生成 DID
2. ✅ 注册用户
3. ✅ 用户登录
4. ✅ 验证 Token
5. ✅ 注册连接器
6. ✅ 列出连接器
7. ✅ 创建数据产品
8. ✅ 列出数据产品
9. ✅ 创建合约
10. ✅ 列出合约

### 方法二：Swagger UI 界面测试

1. 访问 http://localhost:8085/docs
2. 按以下顺序测试：

#### Step 1: 生成 DID
- **端点**: `POST /api/v1/identity/did/generate`
- **操作**: 点击 "Try it out" → "Execute"
- **保存**: 复制响应中的 `did`, `privateKey`, `didDocument`

#### Step 2: 注册用户
- **端点**: `POST /api/v1/auth/register`
- **请求体**:
  ```json
  {
    "did": "did:example:connector...",  // 从 Step 1 获取
    "signature": "demo-signature-12345",
    "username": "测试用户",
    "email": "test@example.com"
  }
  ```
- **保存**: 复制响应中的 `token`

#### Step 3: 认证后续请求
- 点击页面右上角的 "Authorize" 按钮
- 输入: `Bearer your-token-here`
- 点击 "Authorize"

#### Step 4: 注册连接器
- **端点**: `POST /api/v1/identity/did/register`
- **请求体**:
  ```json
  {
    "did": "did:example:connector...",  // 再次生成新的 DID
    "display_name": "测试连接器",
    "data_space_id": "abc-123-def",     // 从 init_db.py 获取
    "did_document": { ... }             // 从生成的 DID 获取
  }
  ```

#### Step 5: 创建数据产品
- **端点**: `POST /api/v1/offerings`
- **表单数据**:
  - `connector_id`: 从 Step 4 获取
  - `title`: "测试数据集"
  - `description`: "测试描述"
  - `data_type`: "local_file"
  - `access_policy`: "Open"
  - `storage_meta`: `{"file_path": "/data/test.csv", "protocol": "local"}`

#### Step 6: 创建合约
- **端点**: `POST /api/v1/contracts`
- **请求体**:
  ```json
  {
    "name": "数据共享合约",
    "policy": "按次付费",
    "provider_connector_id": "provider-id",
    "consumer_connector_id": "consumer-id",
    "status": "active"
  }
  ```

### 方法三：使用 curl 命令

```bash
# 1. 生成 DID
curl -X POST http://localhost:8085/api/v1/identity/did/generate

# 2. 注册用户
curl -X POST http://localhost:8085/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "did": "did:example:connector...",
    "signature": "demo-signature-12345",
    "username": "测试用户",
    "email": "test@example.com"
  }'

# 3. 登录
curl -X POST http://localhost:8085/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "did": "did:example:connector...",
    "signature": "demo-signature-12345"
  }'

# 4. 验证 Token（替换 YOUR_TOKEN）
curl -X GET http://localhost:8085/api/v1/auth/verify \
  -H "Authorization: Bearer YOUR_TOKEN"

# 5. 列出连接器
curl -X GET http://localhost:8085/api/v1/identity/connectors \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 方法四：使用 Postman

1. 导入集合：创建新的 Collection
2. 设置环境变量：
   - `base_url`: `http://localhost:8085`
   - `token`: (在登录后保存)
3. 按照 API 端点说明依次测试

---

## 📚 API 端点说明

### 认证模块 (auth)

| 方法 | 端点 | 描述 | 需要认证 |
|------|------|------|----------|
| POST | `/api/v1/auth/register` | 用户注册 | ❌ |
| POST | `/api/v1/auth/login` | 用户登录 | ❌ |
| GET | `/api/v1/auth/verify` | 验证 Token | ✅ |

### 身份与连接器模块 (identity)

| 方法 | 端点 | 描述 | 需要认证 |
|------|------|------|----------|
| POST | `/api/v1/identity/did/generate` | 生成 DID | ❌ |
| POST | `/api/v1/identity/did/register` | 注册连接器 | ✅ |
| GET | `/api/v1/identity/connectors` | 列出连接器 | ✅ |

### 数据产品模块 (offerings)

| 方法 | 端点 | 描述 | 需要认证 |
|------|------|------|----------|
| POST | `/api/v1/offerings` | 创建数据产品 | ✅ |
| GET | `/api/v1/offerings` | 列出数据产品 | ✅ |

### 合约模块 (contracts)

| 方法 | 端点 | 描述 | 需要认证 |
|------|------|------|----------|
| POST | `/api/v1/contracts` | 创建合约 | ✅ |
| GET | `/api/v1/contracts` | 列出合约 | ✅ |

---

## 🔍 故障排查

### 问题 1: 模块导入错误
```
ModuleNotFoundError: No module named 'passlib'
```
**解决方案**:
```bash
pip install passlib[bcrypt]
```

### 问题 2: 数据库错误
```
sqlalchemy.exc.OperationalError: no such table: users
```
**解决方案**:
```bash
python init_db.py
```

### 问题 3: Token 过期
```
{"detail": "Token has expired"}
```
**解决方案**: 重新登录获取新 Token

### 问题 4: 端口被占用
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8085)
```
**解决方案**:
```bash
# 方法 1: 更换端口
uvicorn app.main:app --reload --port 8086

# 方法 2: 查找并关闭占用进程 (Windows)
netstat -ano | findstr :8085
taskkill /PID <进程ID> /F
```

### 问题 5: Data Space 不存在
```
{"detail": "Data space not found"}
```
**解决方案**: 运行 `python init_db.py` 创建默认数据空间

### 问题 6: JSON 解析错误
```
json.decoder.JSONDecodeError: Expecting value
```
**解决方案**: 检查 `storage_meta` 是否为有效的 JSON 字符串：
```json
{"file_path": "/data/test.csv", "protocol": "local"}
```

---

## 📝 测试检查清单

- [ ] 依赖已安装 (`pip list`)
- [ ] 数据库已初始化 (`init_db.py`)
- [ ] 服务器正常启动 (http://localhost:8085/docs)
- [ ] 可以生成 DID
- [ ] 可以注册用户
- [ ] 可以登录并获取 Token
- [ ] Token 验证通过
- [ ] 可以注册连接器
- [ ] 可以创建数据产品
- [ ] 可以创建合约
- [ ] 所有列表接口正常

---

## 🎯 下一步

1. **实现真实的签名验证**
   - 使用 cryptography 库实现 Ed25519 签名验证
   - 从 DID Document 中提取公钥进行验证

2. **添加更多功能**
   - 文件上传和存储
   - 数据产品搜索和过滤
   - 合约状态管理
   - 访问日志记录

3. **安全增强**
   - 添加速率限制
   - 添加 CORS 配置
   - 添加请求日志
   - 添加输入验证

4. **生产部署**
   - 使用 PostgreSQL 替代 SQLite
   - 配置 HTTPS
   - 使用 Docker 容器化
   - 配置环境变量管理

---

## 📞 联系与支持

如有问题，请检查：
1. 日志输出
2. Swagger UI 的错误信息
3. 数据库文件是否存在
4. .env 配置是否正确

---

**祝测试顺利！** 🚀
