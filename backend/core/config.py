from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from dotenv import load_dotenv

# Absolute path to the .env file in project root
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # SQLite
    DATABASE_URL: str = "sqlite:////tmp/rag.db" if os.environ.get("VERCEL") else "sqlite:///./rag.db"

    # Qdrant Local
    QDRANT_PATH: str = ":memory:"
    QDRANT_COLLECTION_NAME: str = "documents"

    # LLM Settings
    LLM_PROVIDER: str = "groq"  # "groq" or "gemini"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    @property
    def LLM_API_KEY(self) -> str:
        if self.LLM_PROVIDER == "groq":
            return self.GROQ_API_KEY or ""
        return self.GEMINI_API_KEY or ""

    @property
    def LLM_BASE_URL(self) -> str:
        if self.LLM_PROVIDER == "groq":
            return "https://api.groq.com/openai/v1"
        return "https://generativelanguage.googleapis.com/v1beta/openai/"

    # Embedding
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(env_file=env_path, extra="ignore")

settings = Settings()
