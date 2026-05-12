from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT ───────────────────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── Storage ───────────────────────────────────────────────────────────────
    TEMP_DIR: str = "./data/temp"
    IMAGE_DIR: str = "./data/images"
    UPLOAD_DIR: str = "./data/images"

    # ── AI ────────────────────────────────────────────────────────────────────
    FACE_SIMILARITY_THRESHOLD: float = 0.65
    FAISS_NPROBE: int = 10
  
    # NEW (optional but useful)
    # FAISS_INDEX_DIR: str = "./faiss_indexes"
    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000


settings = Settings()