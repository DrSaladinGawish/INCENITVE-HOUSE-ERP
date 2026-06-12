from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "EventCore ERP"
    app_version: str = "1.0.0"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./eventcore.db"
    redis_url: str = ""
    secret_key: str = "eventcore-dev-secret-key-change-in-production"
    app_port: int = 8001

    bio_erp_base_url: str = "http://localhost:8000"
    bio_erp_api_key: str = ""
    bio_erp_vendor_sync_interval: int = 3600
    bio_erp_gl_sync_enabled: bool = True
    bio_erp_po_approval_workflow: bool = False

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000", "http://localhost:8001"]

    class Config:
        env_file = ".env"


settings = Settings()
