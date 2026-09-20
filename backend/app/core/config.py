import os
import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union

_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_CONFIG_DIR)
_BACKEND_DIR = os.path.dirname(_APP_DIR)
_ROOT_DIR = os.path.dirname(_BACKEND_DIR)

def _find_env_file() -> str:
    for path in [
        os.path.join(_BACKEND_DIR, ".env"),
        os.path.join(_ROOT_DIR, ".env"),
        ".env"
    ]:
        if os.path.isfile(path):
            return path
    return ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        extra="ignore"
    )

    APP_NAME: str = "DOC-Lingo"
    APP_ENV: str = "development"
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v
    
    # RAG parameters
    CHUNK_SIZE: int = 900
    CHUNK_OVERLAP: int = 120
    TOP_K: int = 4
    RETRIEVAL_K: int = 16
    RERANK_K: int = 8
    FINAL_CONTEXT_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.35
    
    # Storage
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "data", "uploads")
    CHROMA_PERSIST_DIR: str = os.path.join(BASE_DIR, "data", "chroma")
    COLLECTION_NAME: str = "doc_lingo_collection"
    MAX_FILE_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx"]
    
    # Authentication & Multi-User Security
    JWT_SECRET: str = "doc-lingo-super-secure-jwt-secret-key-2026"
    TOKEN_EXPIRE_HOURS: int = 720  # 30 days
    USER_DATA_FILE: str = os.path.join(BASE_DIR, "data", "users_registry.json")
    
    # Embedding Configuration
    # Provider: "auto" | "gemini" | "sentence-transformers"
    EMBEDDING_PROVIDER: str = "auto"
    # BAAI/bge-m3 or sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DEVICE: str = "cpu"
    
    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # ollama | openai | gemini | mock
    LLM_MODEL: str = "llama3.2"
    LLM_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
