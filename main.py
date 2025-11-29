#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI4S-Discovery 主入口文件
支持多种运行模式：Web界面、API服务、命令行工具
"""

import os
import sys
import argparse
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# 加载环境变量
load_dotenv()

from src.core.config import settings
from src.utils.device_manager import DeviceManager
from src.utils.logger_config import setup_logger


def setup_environment():
    """初始化运行环境"""
    # 创建必要的目录
    directories = [
        settings.DATA_DIR,
        settings.LOG_DIR,
        settings.MODEL_DIR,
        settings.CACHE_DIR,
        settings.REPORT_DIR,
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # 配置日志
    setup_logger()
    
    # 检测硬件配置
    device_manager = DeviceManager()
    device_info = device_manager.get_device_info()
    
    logger.info("=" * 60)
    logger.info("AI4S-Discovery 启动")
    logger.info("=" * 60)
    logger.info(f"版本: {settings.APP_VERSION}")
    logger.info(f"环境: {settings.ENVIRONMENT}")
    logger.info(f"设备: {device_info['device']}")
    logger.info(f"CPU: {device_info['cpu_name']}")
    logger.info(f"内存: {device_info['total_memory']:.2f} GB")
    
    if device_info['has_gpu']:
        logger.info(f"GPU: {device_info['gpu_name']}")
        logger.info(f"GPU内存: {device_info['gpu_memory']:.2f} GB")
    else:
        logger.info("GPU: 未检测到CUDA设备，将使用CPU模式")
    
    logger.info("=" * 60)
    
    return device_manager


def run_web_mode():
    """启动Web界面模式"""
    logger.info("启动Web界面模式...")
    
    try:
        import streamlit.web.cli as stcli
        
        # Streamlit应用路径
        app_path = ROOT_DIR / "src" / "web" / "app.py"
        
        sys.argv = [
            "streamlit",
            "run",
            str(app_path),
            "--server.port", str(settings.WEB_PORT),
            "--server.address", settings.WEB_HOST,
            "--theme.base", "light",
            "--theme.primaryColor", "#1f77b4",
        ]
        
        sys.exit(stcli.main())
        
    except Exception as e:
        logger.error(f"Web界面启动失败: {e}")
        sys.exit(1)


def run_api_mode():
    """启动API服务模式"""
    logger.info("启动API服务模式...")
    
    try:
        import uvicorn
        from src.api.main import app
        
        uvicorn.run(
            app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            workers=settings.API_WORKERS,
            log_level=settings.LOG_LEVEL.lower(),
        )
        
    except Exception as e:
        logger.error(f"API服务启动失败: {e}")
        sys.exit(1)


def run_cli_mode(args):
    """启动命令行模式"""
    logger.info("启动命令行模式...")
    
    try:
        from src.cli.main import CLI
        
        cli = CLI()
        
        if args.query:
            # 执行研究查询
            result = cli.research(
                query=args.query,
                domains=args.domains.split(',') if args.domains else None,
                depth=args.depth,
                include_patents=args.patents,
                generate_hypotheses=args.hypotheses,
                trl_assessment=args.trl,
            )
            
            # 输出结果
            if args.output:
                cli.export_report(result, args.output, args.format)
                logger.info(f"报告已保存至: {args.output}")
            else:
                cli.print_result(result)
        
        elif args.interactive:
            # 交互式模式
            cli.interactive_mode()
        
        else:
            logger.error("请指定 --query 或 --interactive 参数")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"命令行模式执行失败: {e}")
        sys.exit(1)


def run_init_mode():
    """初始化数据库和模型"""
    logger.info("初始化系统...")
    
    try:
        from src.scripts.init_database import init_database
        from src.scripts.download_models import download_models
        
        # 初始化数据库
        logger.info("初始化数据库...")
        init_database()
        
        # 下载模型
        logger.info("下载必要的模型...")
        download_models()
        
        logger.success("系统初始化完成！")
        
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI4S-Discovery - 科研创新辅助工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # Web界面模式
  python main.py --mode web
  
  # API服务模式
  python main.py --mode api
  
  # 命令行查询
  python main.py --mode cli --query "钙钛矿太阳能电池稳定性研究"
  
  # 交互式命令行
  python main.py --mode cli --interactive
  
  # 初始化系统
  python main.py --mode init
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['web', 'api', 'cli', 'init'],
        default='web',
        help='运行模式 (默认: web)'
    )
    
    # CLI模式参数
    parser.add_argument('--query', type=str, help='研究查询内容')
    parser.add_argument('--domains', type=str, help='研究领域（逗号分隔）')
    parser.add_argument('--depth', type=str, default='comprehensive', 
                       choices=['quick', 'standard', 'comprehensive'],
                       help='分析深度')
    parser.add_argument('--patents', action='store_true', help='包含专利分析')
    parser.add_argument('--hypotheses', action='store_true', help='生成创新假设')
    parser.add_argument('--trl', action='store_true', help='进行TRL评估')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--format', type=str, default='pdf',
                       choices=['pdf', 'docx', 'html', 'markdown'],
                       help='报告格式')
    parser.add_argument('--interactive', action='store_true', help='交互式模式')
    
    args = parser.parse_args()
    
    # 初始化环境
    setup_environment()
    
    # 根据模式启动
    if args.mode == 'web':
        run_web_mode()
    elif args.mode == 'api':
        run_api_mode()
    elif args.mode == 'cli':
        run_cli_mode(args)
    elif args.mode == 'init':
        run_init_mode()


if __name__ == "__main__":
    main()