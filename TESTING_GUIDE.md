# TDS Connector API 测试指南


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
```

---

## 📦 安装依赖

```bash
# 进入项目目录
cd D:\wjh\tds-connector-ui-backend

# 安装所有依赖
pip install -r requirements.txt
```

## 🗄️ 初始化数据库

### 使用初始化脚本

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

**重要：保存输出的 `data_space_id`，后续测试需要使用！**



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

### 方法一：自动化测试脚本

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



---

##  API 端点说明

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


##  下一步

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

