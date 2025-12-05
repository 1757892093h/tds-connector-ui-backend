from fastapi import FastAPI

from .config import settings
from .routers import auth, identity, offerings, contracts,policy_templates, contract_templates, data_requests

app = FastAPI(title=settings.app_name)

app.include_router(auth.router)
app.include_router(identity.router)
app.include_router(offerings.router)
app.include_router(contracts.router)
app.include_router(policy_templates.router)
app.include_router(contract_templates.router)
app.include_router(data_requests.router)

@app.get("/")
async def root():
    return {"message": "TDS Connector API"}