from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "IncentiveHouse ERP"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 9001

    # SQL Server
    SQL_SERVER: str = "localhost"
    SQL_DATABASE: str = "IHE_ERP"
    SQL_USERNAME: str = "sa"
    SQL_PASSWORD: str = "IHE_ERP_2024!"
    SQL_DRIVER: str = "ODBC Driver 18 for SQL Server"

    @property
    def DATABASE_URL(self) -> str:
        return f"mssql+pyodbc://{self.SQL_USERNAME}:{self.SQL_PASSWORD}@{self.SQL_SERVER}/{self.SQL_DATABASE}?driver={self.SQL_DRIVER}&TrustServerCertificate=yes"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return self.DATABASE_URL

    # JWT
    JWT_SECRET: str = "ihe-erp-jwt-secret-key-2024"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Admin seed
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_EMAIL: str = "admin@incentivehouse.com"
    ADMIN_FULL_NAME: str = "System Administrator"

    # CORS — comma-separated in .env, parsed as list
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self) -> List[str]:
        raw = self.CORS_ORIGINS.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    # Paths
    ARCHIVE_ROOT: str = "D:\\Data_Sources\\docs"
    USB_ROOT: str = "D:\\"
    USB_BASE_PATH: str = "INCENTIVE HOUSE OF EGYPT\\Book Keeping\\Master Data"

    # SSL (optional — set in .env for production)
    SSL_CERTFILE: str = ""
    SSL_KEYFILE: str = ""


settings = Settings()
