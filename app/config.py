from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "tds-connector-api"
    env: str = "development"
    api_prefix: str = "/api/v1"

    secret_key: str
    access_token_expire_minutes: int = 720

    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()