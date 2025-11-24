import hashlib
import secrets
from datetime import datetime, timezone


class DIDService:
    @staticmethod
    def generate_did() -> dict:
          # demo did实现
          private_key = secrets.token_hex(32)
          did = f"did:example:connector{secrets.token_hex(8)}"
          public_key = hashlib.sha256(private_key.encode()).hexdigest()

          did_document = {
              "@context": ["https://www.w3.org/ns/did/v1"],
              "id": did,
              "verificationMethod": [
                  {
                      "id": f"{did}#keys-1",
                      "type": "Ed25519VerificationKey2018",
                      "controller": did,
                      "publicKeyMultibase": public_key,
                  }
              ],
              "authentication": [f"{did}#keys-1"],
              "service": [
                  {
                      "id": f"{did}#connector-endpoint",
                      "type": "ConnectorService",
                      "serviceEndpoint": f"https://{did}.example.com/api",
                  }
              ],
          }

          return {
              "did": did,
              "publicKey": public_key,
              "privateKey": private_key,
              "didDocument": did_document,
              "createdAt": datetime.now(timezone.utc).isoformat(),
          }