#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型下载脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0， str(ROOT_DIR))

from loguru import logger
from src.core.config import settings


def download_models():
    """下载必要的模型"""
    try:
        logger.info("开始下载模型...")
        
        # 创建模型目录
        model_dir = Path(settings.MODEL_PATH)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"模型目录: {model_dir}")
        
        # 这里可以添加实际的模型下载逻辑
        # 例如：从HuggingFace下载预训练模型
        
        logger.info("提示：模型将在首次使用时自动下载")
        logger.info(f"嵌入模型: {settings.EMBEDDING_MODEL}")
        logger.info(f"LLM模型: {settings.MINICPM_MODEL_NAME}")
        
        logger.success("模型准备完成！")
        return True
        
    except Exception as e:
        logger.error(f"模型下载失败: {e}")
        return False


if __name__ == "__main__":
    download_models()
