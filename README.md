#启动后端
conda activate tds-backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8085

当前设计的模型结构：
users
├─ id (uuid)
├─ did (unique)                    # 登录/注册用的 DID
├─ username / email (可选)
└─ created_at

data_spaces
├─ id
├─ code (如 "CN-SH")              # 你前端 DataSpaceSwitcher 用的 code
└─ name

connectors
├─ id
├─ did (unique)                   # 连接器自身的 DID
├─ owner_user_id (FK users.id)    # 连接器归属的用户
├─ data_space_id (FK data_spaces.id)
├─ display_name
├─ status (registered / pending…)
├─ did_document (JSON)
└─ created_at

data_offerings
├─ id
├─ connector_id (FK connectors.id)
├─ title / description
├─ data_type (local_file/s3/nas/restful)
├─ access_policy
├─ storage_meta (JSON)            # bucket/objectKey/path 等
├─ registration_status
├─ created_at

contracts
├─ id
├─ provider_connector_id (FK connectors.id)
├─ consumer_connector_id (FK connectors.id)
├─ name / policy / status
├─ contract_address / expires_at
└─ created_at

contract_events / monitoring (可选扩展)