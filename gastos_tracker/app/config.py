from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./gastos.db"
    SANTANDER_RUT: str = ""
    SANTANDER_PASSWORD: str = ""
    FALABELLA_RUT: str = ""
    FALABELLA_PASSWORD: str = ""
    SECRET_KEY: str = "dev-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8
    ALERT_EMAIL: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
