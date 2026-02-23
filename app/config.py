from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    allow_origins: List[str] = ["https://localhost:8000",
                                "https://fastapi-l3f5.onrender.com/"]

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
