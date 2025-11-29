#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目初始化脚本
用于首次部署时初始化数据库、创建必要目录等
"""

import os
import sys
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
        settings.REPORTS_DIR,
        Path(settings.SQLITE_DB_PATH).parent,
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ 创建目录: {directory}")


def init_database():
    """初始化数据库"""
    logger.info("初始化SQLite数据库...")
    
    try:
        db = SQLiteManager()
        logger.success("✓ SQLite数据库初始化完成")
        
        # 创建默认管理员用户（仅用于演示）
        try:
            import hashlib
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            db.create_user(
                username="admin",
                password_hash=password_hash,
                email="admin@ai4s-discovery.com",
                role="admin"
            )
            logger.info("✓ 创建默认管理员用户: admin / admin123")
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
    logger.info(f"✓ 检测到设备: {device_info['device_type']} - {device_info['device_name']}")
    logger.info(f"  内存: {device_info['memory_used']:.1f}GB / {device_info['memory_total']:.1f}GB")
    
    if device_info['device_type'] == 'cuda':
        logger.success(f"✓ GPU可用: {device_info['device_name']}")
        logger.info(f"  GPU内存: {device_info.get('gpu_memory_used', 0):.1f}GB / {device_info.get('gpu_memory_total', 0):.1f}GB")
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


def print_next_steps():
    """打印后续步骤"""
    logger.info("\n" + "="*80)
    logger.info("初始化完成！后续步骤：")
    logger.info("="*80)
    
    print("""
1. 配置环境变量（可选）：
   - 复制 .env.example 为 .env
   - 填写API密钥等配置信息

2. 启动服务：
   
   方式1 - Docker部署（推荐）：
   docker-compose up -d
   
   方式2 - 直接运行：
   python main.py
   
   方式3 - Web界面：
   streamlit run src/web/app.py
   
   方式4 - API服务：
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000

3. 使用CLI工具：
   python -m src.cli.main search "your query"
   python -m src.cli.main analyze "your research topic"
   python -m src.cli.main status

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
        
        # 5. 打印后续步骤
        print_next_steps()
        
        logger.success("\n✓ 项目初始化成功！")
        
    except Exception as e:
        logger.error(f"\n✗ 初始化失败: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()