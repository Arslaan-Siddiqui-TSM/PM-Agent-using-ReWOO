from __future__ import annotations
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings sourced from environment variables (via .env)."""

    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field("gpt-4o-mini", env="OPENAI_MODEL")
    EMBEDDING_MODEL: str = Field("text-embedding-3-small", env="EMBEDDING_MODEL")
    CHROMA_PERSIST_DIRECTORY: str = Field("./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    CHROMA_COLLECTION_NAME: str = Field("docs_collection", env="CHROMA_COLLECTION_NAME")
    MAX_CHUNK_SIZE: int = Field(1000, env="MAX_CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(200, env="CHUNK_OVERLAP")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("OPENAI_API_KEY")
    def check_api_key(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("OPENAI_API_KEY must be set in environment or .env file")
        return v

settings = Settings()
