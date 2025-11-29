#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0， str(ROOT_DIR))

from loguru import logger
from src.database.sqlite_manager import db_manager


def init_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # SQLite数据库已在导入时自动初始化
        logger.success("SQLite数据库初始化完成")
        
        # 这里可以添加其他数据库的初始化逻辑
        # 例如：Neo4j, Redis等
        
        logger.success("数据库初始化完成！")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


if __name__ == "__main__":
    init_database()
