import secrets
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import DIDRecord
#DIDService 负责生成和注册；demo阶段存储在 SQLite
class DIDService:
    @staticmethod
    def generate_did():
        identifier = secrets.token_hex(16)
        did = f"did:tds:connector:{identifier}"
        private_key = secrets.token_hex(32)
        public_key = hashlib.sha256(private_key.encode()).hexdigest()

        did_document = {
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": did,
            "verificationMethod": [{
                "id": f"{did}#keys-1",
                "type": "Ed25519VerificationKey2020",
                "controller": did,
                "publicKeyMultibase": public_key
            }],
            "authentication": [f"{did}#keys-1"],
            "service": [{
                "id": f"{did}#service-1",
                "type": "DataConnectorService",
                "serviceEndpoint": "https://connector.example.com/api"
            }]
        }

        return {
            "did": did,
            "didDocument": did_document,
            "publicKey": public_key,
            "privateKey": private_key,
        }

    @staticmethod
    async def register_did(session: AsyncSession, did: str, did_document: dict):
        record = await session.get(DIDRecord, did)
        if record:
            return False
        new_record = DIDRecord(did=did, document=json.dumps(did_document))
        session.add(new_record)
        await session.commit()
        return True

    @staticmethod
    async def get_did(session: AsyncSession, did: str):
        stmt = select(DIDRecord).where(DIDRecord.did == did)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        return record