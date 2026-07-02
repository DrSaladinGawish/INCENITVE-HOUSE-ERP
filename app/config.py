from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    APP_NAME: str = "IncentiveHouse ERP"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 9001

    # MySQL (fallback)
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "RootPass123!"
    MYSQL_DATABASE: str = "IncentiveHouse_ERP"

    @property
    def MYSQL_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    # SQL Server
    SQL_SERVER: str = "localhost"
    SQL_DATABASE: str = "IHE_ERP"
    SQL_USERNAME: str = "sa"
    SQL_PASSWORD: str = "IHE_ERP_2024!"
    SQL_DRIVER: str = "ODBC Driver 18 for SQL Server"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mssql+pyodbc://{self.SQL_USERNAME}:{self.SQL_PASSWORD}@{self.SQL_SERVER}/{self.SQL_DATABASE}"
            f"?driver={self.SQL_DRIVER}&TrustServerCertificate=yes&timeout=5&loginTimeout=5"
        )

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
    ARCHIVE_ROOT: str = "D:\\IncentiveHouse_Data\\Data_Sources\\docs"
    USB_ROOT: str = "D:\\"
    USB_BASE_PATH: str = "INCENTIVE HOUSE OF EGYPT\\Book Keeping\\Master Data"

    # Redis (optional — required for multi-worker rate limiting & caching)
    REDIS_URL: str = ""
    PROMETHEUS_MULTIPROC_DIR: str = "data/metrics"

    # Workers (used to adjust per-process rate limits when no Redis)
    UVICORN_WORKERS: int = 4

    # SSL (optional — set in .env for production)
    SSL_CERTFILE: str = ""
    SSL_KEYFILE: str = ""


settings = Settings()
