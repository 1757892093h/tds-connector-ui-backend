## 1. 启动后端

```bash
# 激活环境并启动服务
conda activate tds-backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8085
```

## 2. API端点
所有 API 端点前缀为 `/api/v1`

### 认证 (auth)
- `POST /api/v1/auth/register` - 用户注册（基于 DID）
- `POST /api/v1/auth/login` - 用户登录（基于 DID）
- `GET /api/v1/auth/verify` - 验证 JWT Token

### 身份管理 (identity)
- `POST /api/v1/identity/did/generate` - 生成 DID
- `POST /api/v1/identity/did/register` - 注册连接器
- `GET /api/v1/identity/connectors` - 查询连接器列表
- `GET /api/v1/identity/data-spaces` - 查询数据空间列表

### 数据资源 (offerings)
- `POST /api/v1/offerings` - 创建数据资源
- `GET /api/v1/offerings` - 查询数据资源列表

### 策略模板 (policy-templates)
- `POST /api/v1/policy-templates` - 创建策略模板
- `GET /api/v1/policy-templates` - 查询策略模板列表
- `GET /api/v1/policy-templates/{id}` - 获取策略模板详情
- `PUT /api/v1/policy-templates/{id}` - 更新策略模板
- `DELETE /api/v1/policy-templates/{id}` - 删除策略模板

### 合约模板 (contract-templates)
- `POST /api/v1/contract-templates` - 创建合约模板
- `GET /api/v1/contract-templates` - 查询合约模板列表
- `GET /api/v1/contract-templates/{id}` - 获取合约模板详情
- `PUT /api/v1/contract-templates/{id}` - 更新合约模板
- `DELETE /api/v1/contract-templates/{id}` - 删除合约模板

### 数据请求 (data-requests)
- `POST /api/v1/data-requests` - 创建数据访问请求
- `GET /api/v1/data-requests` - 查询数据请求列表（支持 role 参数）
- `GET /api/v1/data-requests/{id}` - 获取数据请求详情
- `PUT /api/v1/data-requests/{id}/approve` - 批准数据请求
- `PUT /api/v1/data-requests/{id}/reject` - 拒绝数据请求

### 数据合约 (contracts)
- `POST /api/v1/contracts` - 创建数据合约
- `GET /api/v1/contracts` - 查询数据合约列表
- `PUT /api/v1/contracts/{id}/confirm` - 确认合约（消费者）
- `POST /api/v1/contracts/{id}/deploy` - 部署合约到区块链


## 3.认证机制
### DID 基础认证

1. **注册流程**：
   - 客户端生成 DID
   - 使用 DID 私钥对 `"Register:{did}"` 签名
   - 发送 DID、签名、用户名、邮箱到 `/api/v1/auth/register`
   - 后端验证签名后创建用户并返回 JWT Token

2. **登录流程**：
   - 使用 DID 私钥对 `"Login:{did}"` 签名
   - 发送 DID 和签名到 `/api/v1/auth/login`
   - 后端验证签名后返回 JWT Token

3. **API 调用**：
   - 在请求头中添加：`Authorization: Bearer <token>`
   - Token 有效期：720 分钟（12 小时）
## 4.开发指南
### 添加新的 API 端点

1. 在 `app/routers/` 创建或修改路由文件
2. 定义路由函数，使用 `@router.get/post/put/delete` 装饰器
3. 在 `app/main.py` 中注册路由：thon
   from .routers import your_router
   app.include_router(your_router.router)
### 代码结构

- **models.py**: SQLAlchemy ORM 模型
- **schemas.py**: Pydantic 数据验证模型
- **routers/**: API 路由处理
- **deps.py**: 依赖注入（如 `get_current_user`）
- **security.py**: JWT 和签名验证

## 5.数据模型，核心实体关系图
```text
users (用户)
├── connectors (连接器)
│   ├── data_offerings (数据资源)
│   ├── policy_templates (策略模板)
│   │   └── policy_rules (策略规则)
│   ├── contract_templates (合约模板)
│   │   └── contract_template_policies (关联表)
│   └── data_requests (数据请求)
│
data_spaces (数据空间)
└── connectors (连接器)

contracts (数据合约)
├── provider_connector (提供者连接器)
├── consumer_connector (消费者连接器)
├── contract_template (合约模板)
├── data_offering (数据资源)
└── data_request (数据请求)

1. users (用户)
id (uuid) - 主键
did (string, unique) - 去中心化身份标识，用于登录/注册
username (string, optional) - 用户名
email (string, optional) - 邮箱
created_at (datetime) - 创建时间

2.data_spaces (数据空间)
id (uuid) - 主键
code (string, unique) - 数据空间代码（如 "CN-SH"）
name (string) - 数据空间名称
description (text, optional) - 描述

3. connectors (连接器)
id (uuid) - 主键
did (string, unique) - 连接器 DID
display_name (string) - 显示名称
status (string) - 状态（registered/pending...）
did_document (json) - DID 文档
owner_user_id (fk) - 所属用户
data_space_id (fk) - 所属数据空间
created_at (datetime) - 创建时间

4.data_offerings (数据资源)
id (uuid) - 主键
connector_id (fk) - 所属连接器
title (string) - 标题
description (text) - 描述
data_type (string) - 数据类型（local_file/s3/nas/restful）
access_policy (string) - 访问策略
storage_meta (json) - 存储元数据（bucket/objectKey/path 等）
registration_status (string) - 注册状态
created_at (datetime) - 创建时间

5. policy_templates (策略模板)
id (uuid) - 主键
connector_id (fk) - 所属连接器
name (string) - 模板名称
description (text) - 描述
category (string) - 类别
severity (string) - 严重程度
enforcement_type (string) - 执行类型
created_at (datetime) - 创建时间
updated_at (datetime, optional) - 更新时间

6. policy_rules (策略规则)
id (uuid) - 主键
policy_template_id (fk) - 所属策略模板
type (string) - 规则类型
name (string) - 规则名称
description (text) - 描述
value (string) - 规则值
unit (string, optional) - 单位
is_active (bool) - 是否激活
created_at (datetime) - 创建时间

7. contract_templates (合约模板)
id (uuid) - 主键
connector_id (fk) - 所属连接器
name (string) - 模板名称
description (text) - 描述
contract_type (string) - 合约类型
status (string) - 状态（draft/active）
usage_count (int) - 使用次数
created_at (datetime) - 创建时间
updated_at (datetime, optional) - 更新时间

8. contract_template_policies (合约模板-策略模板关联表)
contract_template_id (fk) - 合约模板 ID
policy_template_id (fk) - 策略模板 ID
复合主键

9. data_requests (数据请求)
id (uuid) - 主键
data_offering_id (fk) - 请求的数据资源
consumer_connector_id (fk) - 消费者连接器
purpose (text) - 使用目的
access_mode (string) - 访问模式
status (string) - 状态（pending/approved/rejected）
created_at (datetime) - 创建时间
updated_at (datetime, optional) - 更新时间

10. contracts (数据合约)
id (uuid) - 主键
provider_connector_id (fk) - 提供者连接器
consumer_connector_id (fk) - 消费者连接器
contract_template_id (fk) - 合约模板
data_offering_id (fk) - 数据资源
data_request_id (fk, optional) - 关联的数据请求
name (string) - 合约名称
status (string) - 状态（pending_consumer/active/rejected/expired）
contract_address (string, optional) - 合约地址（区块链）
blockchain_tx_id (string, optional) - 区块链交易 ID
blockchain_network (string) - 区块链网络（默认 Ethereum）
expires_at (datetime, optional) - 过期时间
created_at (datetime) - 创建时间
updated_at (datetime, optional) - 更新时间
```
## 6.业务流程概览
```text
1. 模板准备阶段（提供者）
   ├─ 创建策略模板 (PolicyTemplate)
   │   └─ 定义策略规则 (PolicyRule)
   └─ 创建合约模板 (ContractTemplate)
       └─ 关联策略模板

2. 数据发布阶段（提供者）
   └─ 创建数据资源 (DataOffering)

3. 合约协商阶段（消费者-提供者）
   ├─ 消费者发起数据请求 (DataRequest)
   ├─ 提供者审核请求（approve/reject）
   │   ├─ 同意：创建合约 (Contract)
   │   └─ 拒绝：更新请求状态
   ├─ 消费者确认合约（confirm/reject）
   │   ├─ 同意：状态 → active
   │   └─ 拒绝：状态 → rejected
   └─ 部署到区块链（可选）
```
## 7.详细业务流程
### 7.1 策略模板（PolicyTemplate）只有连接器所有者可以创建/管理
```text
提供者创建策略模板
├─ 定义策略规则（PolicyRule）
│   ├─ 访问期限（access_period）
│   ├─ 访问次数（access_count）
│   ├─ 加密要求（encryption）
│   ├─ IP限制（ip_restriction）
│   └─ 其他规则...
└─ 保存策略模板
```
### 7.2 合约模板（ContractTemplate）只有连接器所有者可以创建/管理
```text
提供者创建合约模板
├─ 选择策略模板组合（多对多关系）
├─ 设置合约类型（single_policy / multi_policy）
└─ 设置状态（draft / active）

状态流转图
draft (草稿)
  ↓ [激活]
active (激活) → 可以被用于创建合约
  ↓ [使用]
usage_count++ (使用次数增加)
```
### 7.3 数据资源（DataOffering）只有连接器所有者可以创建
```text
提供者发布数据资源
├─ 设置数据资源信息
│   ├─ 标题、描述
│   ├─ 数据类型（local_file/s3/nas/restful）
│   ├─ 访问策略（Open/Restricted/Premium）
│   └─ 存储元数据（storage_meta）
└─ 设置注册状态

状态流转图
unregistered (未注册)
  ↓ [注册]
registered (已注册) → 可以被请求
```
### 7.4数据请求（DataRequest）
只有消费者可以创建（验证 consumer_connector_id 属于当前用户）
```text
消费者发起数据请求
├─ 选择数据资源（DataOffering）
├─ 说明使用目的（purpose）
├─ 选择访问模式（api / download）
└─ 状态：pending

提供者审核请求
├─ approve → approved
└─ reject → rejected

状态流转图
pending (待审核)
  ├─ [提供者批准] → approved (已批准) → [创建合约] → completed (已完成)
  └─ [提供者拒绝] → rejected (已拒绝) → [流程终止]
```
### 7.5数据合约（Contract）
```text
提供者创建数据合约
├─ 基于合约模板（ContractTemplate）
├─ 关联数据资源（DataOffering）
├─ 可选关联数据请求（DataRequest，如果提供则必须是 approved）
└─ 状态：pending_consumer

消费者确认合约
├─ confirm → active
└─ reject → rejected

（可选）部署到区块链
└─ 生成 contract_address 和 blockchain_tx_id
```
