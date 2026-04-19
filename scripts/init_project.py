#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目初始化脚本
用于首次部署时初始化数据库、创建必要目录等
"""

import os
import sys
import secrets
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.core.config import settings
from src.database.sqlite_manager import SQLiteManager
from src.utils.device_manager import device_manager


def create_directories():
    """创建必要的目录"""
    logger.info("创建项目目录...")

    directories = [
        settings.DATA_DIR,
        settings.LOG_DIR,
        settings.CACHE_DIR,
        settings.REPORT_DIR,
        Path(settings.SQLITE_PATH).parent,
    ]

    for directory in directories:
        if isinstance(directory, str):
            directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ 创建目录: {directory}")


def init_database():
    """初始化数据库"""
    logger.info("初始化SQLite数据库...")

    try:
        db = SQLiteManager()
        logger.success("✓ SQLite数据库初始化完成")

        # 创建默认管理员用户（仅用于演示）
        # 注意：在生产环境中应使用强密码
        try:
            from src.utils.encryption import encryption_manager

            # 生成安全的随机密码
            admin_password = secrets.token_urlsafe(16)
            password_hash = encryption_manager.hash_password(admin_password)

            db.create_user(
                username="admin",
                password_hash=password_hash,
                email="admin@ai4s-discovery.com",
                role="admin"
            )
            logger.info("✓ 创建默认管理员用户: admin")
            logger.warning(f"⚠ 请立即修改默认管理员密码！自动生成的临时密码: {admin_password}")
            logger.warning("⚠ 请在生产环境中删除此默认管理员用户")

        except Exception as e:
            logger.warning(f"管理员用户可能已存在: {e}")

    except Exception as e:
        logger.error(f"✗ 数据库初始化失败: {e}")
        raise


def check_environment():
    """检查环境配置"""
    logger.info("检查环境配置...")

    # 检查.env文件
    env_file = project_root / ".env"
    if not env_file.exists():
        logger.warning("⚠ .env文件不存在，将使用默认配置")
        logger.info("  建议复制.env.example为.env并配置相关参数")
    else:
        logger.success("✓ .env文件存在")

    # 检查硬件
    device_info = device_manager.get_device_info()
    logger.info(f"✓ 检测到设备: {device_info['device']}")
    logger.info(f"  CPU: {device_info['cpu_name']}")
    logger.info(f"  内存: {device_info['total_memory']:.1f}GB")

    if device_info.get('has_gpu'):
        logger.success(f"✓ GPU可用: {device_info.get('gpu_name', 'Unknown')}")
        logger.info(f"  GPU内存: {device_info.get('gpu_memory', 0):.1f}GB")
    else:
        logger.info("ℹ 未检测到GPU，将使用CPU模式")


def create_sample_config():
    """创建示例配置文件"""
    config_file = project_root / "config.yaml"

    if config_file.exists():
        logger.info("✓ config.yaml已存在")
        return

    logger.info("创建示例配置文件...")

    sample_config = """# AI4S-Discovery 配置文件

# 项目基本信息
project:
  name: "AI4S-Discovery"
  version: "1.0.0"
  environment: "development"

# 数据源配置
data_sources:
  arxiv:
    enabled: true
    max_results: 100
  semantic_scholar:
    enabled: true
    api_key: ""  # 可选，有API Key可提高限额
  pubmed:
    enabled: true
    email: ""  # 建议填写，用于PubMed API
  ieee:
    enabled: false
    api_key: ""  # 需要IEEE Xplore API Key

# 智能体配置
agents:
  coordinator:
    max_retries: 3
    timeout: 300
  search:
    concurrent_requests: 5
    cache_enabled: true
  analysis:
    quality_threshold: 40
    min_citations: 0

# 硬件配置
hardware:
  device: "auto"  # auto/cpu/cuda
  max_memory_gb: 12
  enable_gpu: true

# 日志配置
logging:
  level: "INFO"
  format: "detailed"
  rotation: "100 MB"
"""

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(sample_config)

    logger.success("✓ 创建示例配置文件: config.yaml")


def create_env_example():
    """创建.env.example文件"""
    env_example_file = project_root / ".env.example"

    if env_example_file.exists():
        logger.info("✓ .env.example已存在")
        return

    logger.info("创建.env.example文件...")

    env_example = """# AI4S-Discovery 环境变量配置

# 应用配置
APP_NAME=AI4S-Discovery
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=false

# API配置
API_HOST=0.0.0.0
API_PORT=8000
WEB_HOST=0.0.0.0
WEB_PORT=8501

# API密钥（必填，用于认证）
API_KEY=your_api_key_here

# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# 本地模型配置
USE_LOCAL_MODEL=false
LOCAL_MODEL_PATH=./models/minicpm

# 学术数据源API密钥（可选）
# PUBMED_API_KEY=your_pubmed_api_key
# SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key
# IEEE_API_KEY=your_ieee_api_key

# 硬件配置
DEVICE=auto
MAX_WORKERS=4

# 日志配置
LOG_LEVEL=INFO
"""

    with open(env_example_file, 'w', encoding='utf-8') as f:
        f.write(env_example)

    logger.success("✓ 创建.env.example文件")


def print_next_steps():
    """打印后续步骤"""
    logger.info("\n" + "="*80)
    logger.info("初始化完成！后续步骤：")
    logger.info("="*80)

    print("""
1. 配置环境变量（推荐）：
   - 复制 .env.example 为 .env
   - 填写API密钥等配置信息
   - cp .env.example .env

2. 启动服务：

   方式1 - Docker部署（推荐）：
   docker-compose up -d

   方式2 - 直接运行：
   python main.py --mode web

   方式3 - API服务：
   python main.py --mode api

3. 使用CLI工具：
   python main.py --mode cli --query "your research topic"

4. 访问Web界面：
   http://localhost:8501

5. 访问API文档：
   http://localhost:8000/docs

6. 查看日志：
   tail -f logs/ai4s_discovery.log

更多信息请参考：
- 快速开始: QUICKSTART.md
- 架构文档: ARCHITECTURE.md
- API文档: http://localhost:8000/docs
""")


def main():
    """主函数"""
    logger.info("="*80)
    logger.info("AI4S-Discovery 项目初始化")
    logger.info("="*80)

    try:
        # 1. 检查环境
        check_environment()

        # 2. 创建目录
        create_directories()

        # 3. 初始化数据库
        init_database()

        # 4. 创建示例配置
        create_sample_config()

        # 5. 创建.env.example
        create_env_example()

        # 6. 打印后续步骤
        print_next_steps()

        logger.success("\n✓ 项目初始化成功！")

    except Exception as e:
        logger.error(f"\n✗ 初始化失败: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
