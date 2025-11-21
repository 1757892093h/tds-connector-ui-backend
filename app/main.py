from fastapi import FastAPI

from .config import settings
from .routers import auth, identity, offerings, contracts

app = FastAPI(title=settings.app_name)

app.include_router(auth.router)
app.include_router(identity.router)
app.include_router(offerings.router)
app.include_router(contracts.router)


@app.get("/")
async def root():
    return {"message": "TDS Connector API"}