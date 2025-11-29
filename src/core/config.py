#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统配置管理模块
从环境变量加载配置，提供类型安全的配置访问
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field, validator

# Pydantic v2 兼容性处理
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class 设置(BaseSettings):
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
    TEMPLATE_DIR: Path = ROOT_DIR / "templates"
    
    # ============ 硬件配置 ============
    DEVICE: str = Field(default="auto", env="DEVICE")
    MAX_WORKERS: int = Field(default=4, env="MAX_WORKERS")
    MEMORY_LIMIT: int = Field(default=12, env="MEMORY_LIMIT")
    GPU_MEMORY_LIMIT: int = Field(default=4, env="GPU_MEMORY_LIMIT")
    
    # ============ 数据库配置 ============
    SQLITE_PATH: str = Field(default="./data/metadata.db", env="SQLITE_PATH")
    SQLITE_DB_PATH: str = Field(default="./data/metadata.db", env="SQLITE_PATH")  # 别名兼容
    
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(default="password", env="NEO4J_PASSWORD")
    NEO4J_DATABASE: str = Field(default="ai4s", env="NEO4J_DATABASE")
    
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    
    VECTOR_DB_PATH: str = Field(default="./data/vector_db", env="VECTOR_DB_PATH")
    VECTOR_DB_COLLECTION: str = Field(default="papers", env="VECTOR_DB_COLLECTION")
    
    # ============ API服务配置 ============
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_WORKERS: int = Field(default=1, env="API_WORKERS")
    API_KEY: str = Field(default="dev_api_key", env="API_KEY")
    
    WEB_HOST: str = Field(default="0.0.0.0", env="WEB_HOST")
    WEB_PORT: int = Field(default=8501, env="WEB_PORT")
    
    # ============ 学术数据源配置 ============
    ARXIV_EMAIL: Optional[str] = Field(default=None, env="ARXIV_EMAIL")
    PUBMED_API_KEY: Optional[str] = Field(default=None, env="PUBMED_API_KEY")
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = Field(default=None, env="SEMANTIC_SCHOLAR_API_KEY")
    IEEE_API_KEY: Optional[str] = Field(default=None, env="IEEE_API_KEY")
    SPRINGER_API_KEY: Optional[str] = Field(default=None, env="SPRINGER_API_KEY")
    ELSEVIER_API_KEY: Optional[str] = Field(default=None, env="ELSEVIER_API_KEY")
    
    # ============ 模型配置 ============
    MODEL_PATH: str = Field(default="./models", env="MODEL_PATH")
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
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        env="USER_AGENTS"
    )
    
    HTTP_PROXY: Optional[str] = Field(default=None, env="HTTP_PROXY")
    HTTPS_PROXY: Optional[str] = Field(default=None, env="HTTPS_PROXY")
    
    # ============ 安全配置 ============
    ENCRYPTION_KEY: str = Field(
        default="default_encryption_key_change_me",
        env="ENCRYPTION_KEY"
    )
    JWT_SECRET: str = Field(
        default="default_jwt_secret_change_me",
        env="JWT_SECRET"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION: int = Field(default=3600, env="JWT_EXPIRATION")
    SESSION_TIMEOUT: int = Field(default=3600, env="SESSION_TIMEOUT")
    
    # ============ 日志配置 ============
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_PATH: str = Field(default="./logs", env="LOG_PATH")
    LOG_FORMAT: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        env="LOG_FORMAT"
    )
    LOG_ROTATION: str = Field(default="daily", env="LOG_ROTATION")
    LOG_RETENTION: int = Field(default=30, env="LOG_RETENTION")
    LOG_COMPRESSION: str = Field(default="zip", env="LOG_COMPRESSION")
    
    # ============ 缓存配置 ============
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")
    CACHE_MAX_SIZE: int = Field(default=1024, env="CACHE_MAX_SIZE")
    
    # ============ 任务调度配置 ============
    TASK_QUEUE_MAX_SIZE: int = Field(default=1000, env="TASK_QUEUE_MAX_SIZE")
    TASK_TIMEOUT: int = Field(default=3600, env="TASK_TIMEOUT")
    TASK_CLEANUP_INTERVAL: int = Field(default=300, env="TASK_CLEANUP_INTERVAL")
    
    # ============ 报告生成配置 ============
    REPORT_OUTPUT_PATH: str = Field(default="./reports", env="REPORT_OUTPUT_PATH")
    REPORT_TEMPLATE_PATH: str = Field(default="./templates", env="REPORT_TEMPLATE_PATH")
    REPORT_FORMATS: str = Field(default="pdf,docx,html,markdown", env="REPORT_FORMATS")
    
    # ============ 性能监控配置 ============
    ENABLE_PROMETHEUS: bool = Field(default=True, env="ENABLE_PROMETHEUS")
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    METRICS_INTERVAL: int = Field(default=60, env="METRICS_INTERVAL")
    
    # ============ 文献处理配置 ============
    MAX_PAPERS_PER_DAY: int = Field(default=50000, env="MAX_PAPERS_PER_DAY")
    PAPER_QUALITY_THRESHOLD: int = Field(default=40, env="PAPER_QUALITY_THRESHOLD")
    PDF_PARSE_TIMEOUT: int = Field(default=30, env="PDF_PARSE_TIMEOUT")
    
    # ============ 图谱构建配置 ============
    GRAPH_MAX_NODES: int = Field(default=1000000, env="GRAPH_MAX_NODES")
    GRAPH_CHUNK_SIZE: int = Field(default=10000, env="GRAPH_CHUNK_SIZE")
    GRAPH_UPDATE_INTERVAL: int = Field(default=3600, env="GRAPH_UPDATE_INTERVAL")
    
    # ============ TRL评估配置 ============
    TRL_MODEL_PATH: str = Field(default="./models/trl_classifier", env="TRL_MODEL_PATH")
    TRL_CONFIDENCE_THRESHOLD: float = Field(default=0.8, env="TRL_CONFIDENCE_THRESHOLD")
    
    # ============ 假设生成配置 ============
    HYPOTHESIS_COUNT: int = Field(default=5, env="HYPOTHESIS_COUNT")
    HYPOTHESIS_MIN_CONFIDENCE: float = Field(default=0.7, env="HYPOTHESIS_MIN_CONFIDENCE")
    HYPOTHESIS_TEMPERATURE: float = Field(default=0.8, env="HYPOTHESIS_TEMPERATURE")
    
    # ============ 开发配置 ============
    ENABLE_DEBUG: bool = Field(default=False, env="ENABLE_DEBUG")
    ENABLE_PROFILING: bool = Field(default=False, env="ENABLE_PROFILING")
    VERBOSE_LOGGING: bool = Field(default=False, env="VERBOSE_LOGGING")
    
    @validator("USER_AGENTS")
    def parse_user_agents(cls, v):
        """解析User-Agent列表"""
        if isinstance(v, str):
            return [ua.strip() for ua in v.split(',')]
        return v
    
    @validator("REPORT_FORMATS")
    def parse_report_formats(cls, v):
        """解析报告格式列表"""
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
