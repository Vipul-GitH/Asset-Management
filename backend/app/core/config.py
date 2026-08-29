from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:@127.0.0.1:3306/asset_management"
    secret_key: str = "development-only-change-me"
    upload_dir: str = "./uploads"
    cors_origins: str = (
        "https://localhost:4674,https://labmate.bhasinpathlabs.com:4674"
    )
    public_base_url: str = "https://labmate.bhasinpathlabs.com:4674"
    whatsapp_mode: str = "mock"
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[3] / ".env"), extra="ignore"
    )


settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
