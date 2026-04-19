#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统配置管理模块
从环境变量加载配置，提供类型安全的配置访问
"""

import os
import secrets
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator

# Pydantic v2 兼容性处理
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


def _generate_secure_secret() -> str:
    """生成安全的随机密钥"""
    return secrets.token_urlsafe(32)


class Settings(BaseSettings):
    """系统配置类"""

    # ============ 基础配置 ============
    APP_NAME: str = Field(default="AI4S-Discovery", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")

    # ============ 路径配置 ============
    ROOT_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = ROOT_DIR / "data"
    LOG_DIR: Path = ROOT_DIR / "logs"
    MODEL_DIR: Path = ROOT_DIR / "models"
    CACHE_DIR: Path = ROOT_DIR / "cache"
    REPORT_DIR: Path = ROOT_DIR / "reports"
    REPORTS_DIR: Path = ROOT_DIR / "reports"  # 别名，与init_project.py兼容
    TEMPLATE_DIR: Path = ROOT_DIR / "templates"

    # ============ 硬件配置 ============
    DEVICE: str = Field(default="auto", env="DEVICE")
    MAX_WORKERS: int = Field(default=4, env="MAX_WORKERS")
    MEMORY_LIMIT: int = Field(default=12, env="MEMORY_LIMIT")
    GPU_MEMORY_LIMIT: int = Field(default=4, env="GPU_MEMORY_LIMIT")

    # ============ 数据库配置 ============
    SQLITE_PATH: str = Field(default=str(ROOT_DIR / "data" / "metadata.db"), env="SQLITE_PATH")
    SQLITE_DB_PATH: str = Field(default=str(ROOT_DIR / "data" / "metadata.db"), env="SQLITE_PATH")  # 别名，保持向后兼容

    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(default="password", env="NEO4J_PASSWORD")
    NEO4J_DATABASE: str = Field(default="ai4s", env="NEO4J_DATABASE")

    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")

    VECTOR_DB_PATH: str = Field(default=str(ROOT_DIR / "data" / "vector_db"), env="VECTOR_DB_PATH")
    VECTOR_DB_COLLECTION: str = Field(default="papers", env="VECTOR_DB_COLLECTION")

    # ============ API服务配置 ============
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_WORKERS: int = Field(default=1, env="API_WORKERS")
    API_KEY: str = Field(default="", env="API_KEY")

    WEB_HOST: str = Field(default="0.0.0.0", env="WEB_HOST")
    WEB_PORT: int = Field(default=8501, env="WEB_PORT")

    # ============ 学术数据源配置 ============
    ARXIV_EMAIL: Optional[str] = Field(default=None, env="ARXIV_EMAIL")
    PUBMED_API_KEY: Optional[str] = Field(default=None, env="PUBMED_API_KEY")
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = Field(default=None, env="SEMANTIC_SCHOLAR_API_KEY")
    IEEE_API_KEY: Optional[str] = Field(default=None, env="IEEE_API_KEY")
    SPRINGER_API_KEY: Optional[str] = Field(default=None, env="SPRINGER_API_KEY")
    ELSEVIER_API_KEY: Optional[str] = Field(default=None, env="ELSEVIER_API_KEY")

    # ============ LLM配置 ============
    # OpenAI API配置
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", env="OPENAI_API_BASE")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=2048, env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(default=0.7, env="OPENAI_TEMPERATURE")

    # 本地模型配置
    USE_LOCAL_MODEL: bool = Field(default=False, env="USE_LOCAL_MODEL")
    LOCAL_MODEL_PATH: str = Field(default=str(ROOT_DIR / "models" / "minicpm"), env="LOCAL_MODEL_PATH")

    # LLM通用配置
    LLM_PROVIDER: str = Field(default="openai", env="LLM_PROVIDER")  # openai, local, azure
    LLM_MAX_RETRIES: int = Field(default=3, env="LLM_MAX_RETRIES")
    LLM_TIMEOUT: int = Field(default=60, env="LLM_TIMEOUT")

    # ============ 模型配置 ============
    MODEL_PATH: str = Field(default=str(ROOT_DIR / "models"), env="MODEL_PATH")
    USE_QUANTIZATION: bool = Field(default=True, env="USE_QUANTIZATION")
    QUANTIZATION_BITS: int = Field(default=8, env="QUANTIZATION_BITS")

    MINICPM_MODEL_NAME: str = Field(
        default="openbmb/MiniCPM-2B-sft-bf16",
        env="MINICPM_MODEL_NAME"
    )
    MINICPM_MAX_LENGTH: int = Field(default=2048, env="MINICPM_MAX_LENGTH")

    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    EMBEDDING_DIMENSION: int = Field(default=384, env="EMBEDDING_DIMENSION")

    # ============ 爬虫配置 ============
    CRAWLER_CONCURRENCY: int = Field(default=5, env="CRAWLER_CONCURRENCY")
    CRAWLER_TIMEOUT: int = Field(default=30, env="CRAWLER_TIMEOUT")
    CRAWLER_RETRY: int = Field(default=3, env="CRAWLER_RETRY")
    CRAWLER_DELAY: float = Field(default=1.0, env="CRAWLER_DELAY")

    USER_AGENTS: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        env="USER_AGENTS"
    )

    HTTP_PROXY: Optional[str] = Field(default=None, env="HTTP_PROXY")
    HTTPS_PROXY: Optional[str] = Field(default=None, env="HTTPS_PROXY")

    # ============ 安全配置 ============
    # 生成安全的默认密钥（如果环境变量未设置）
    _default_encryption_key: str = Field(default="", repr=False)
    _default_jwt_secret: str = Field(default="", repr=False)

    @field_validator("SQLITE_PATH", "SQLITE_DB_PATH", mode="before")
    @classmethod
    def _validate_sqlite_path(cls, v):
        if not v or v == "./data/metadata.db":
            return str(Path(__file__).parent.parent.parent / "data" / "metadata.db")
        return v

    @field_validator("REPORT_DIR", "REPORTS_DIR", mode="before")
    @classmethod
    def _validate_report_dir(cls, v):
        if not v or v == "./reports":
            return str(Path(__file__).parent.parent.parent / "reports")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 安全地获取配置值
def _get_secure_config(key: str, env_var: str, default_generator: callable = None) -> str:
    """获取安全的配置值"""
    # 优先使用环境变量
    value = os.getenv(env_var)
    if value:
        return value

    # 检查是否已生成过（存储在文件中）
    config_dir = Path(__file__).parent.parent.parent / "data"
    key_file = config_dir / f".{key}"

    if key_file.exists():
        try:
            with open(key_file, 'r') as f:
                return f.read().strip()
        except Exception:
            pass

    # 生成新值
    if default_generator:
        new_value = default_generator()
    else:
        new_value = secrets.token_urlsafe(32)

    # 保存到文件
    config_dir.mkdir(parents=True, exist_ok=True)
    try:
        with open(key_file, 'w') as f:
            f.write(new_value)
        # 设置文件权限为仅所有者可读（Unix系统）
        try:
            os.chmod(key_file, 0o600)
        except Exception:
            pass
    except Exception:
        pass

    return new_value


# 创建全局配置实例
settings = Settings()


# ============ 全局密钥获取函数 ============
def get_encryption_key() -> str:
    """获取加密密钥"""
    return _get_secure_config("encryption_key", "ENCRYPTION_KEY")


def get_jwt_secret() -> str:
    """获取JWT密钥"""
    return _get_secure_config("jwt_secret", "JWT_SECRET")


# 导出便捷函数
def get_setting(key: str, default: str = None) -> str:
    """获取配置值"""
    return getattr(settings, key, default)
