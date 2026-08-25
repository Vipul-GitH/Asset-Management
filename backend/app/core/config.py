from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:@127.0.0.1:3306/asset_management"
    secret_key: str = "development-only-change-me"
    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:8000"
    public_base_url: str = "http://labmate.bhasinpathlabs.com:9010"
    whatsapp_mode: str = "mock"
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[3] / ".env"), extra="ignore"
    )


settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
