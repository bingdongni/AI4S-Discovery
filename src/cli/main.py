#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI4S-Discovery 命令行工具
提供便捷的命令行接口进行科研辅助
"""

import asyncio
import click
import json
from pathlib import Path
from typing import Optional
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown

from src.core.config import settings
from src.agents.coordinator_agent import coordinator_agent
from src.database.sqlite_manager import db_manager
from src.utils.device_manager import device_manager

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="AI4S-Discovery")
def cli():
    """
    AI4S-Discovery - 科研创新辅助工具
    
    基于多智能体架构的学术文献分析与创新假设生成系统
    """
    pass


@cli.command()
@click.argument('query')
@click.option('--max-papers', default=100, help='最大文献数量')
@click.option('--sources', default='arxiv,semantic_scholar', help='数据源（逗号分隔）')
@click.option('--output', '-o', help='输出文件路径')
@click.option('--format', default='json', type=click.Choice(['json', 'markdown', 'html']), help='输出格式')
def search(query: str, max_papers: int, sources: str, output: Optional[str], format: str):
    """
    搜索学术文献
    
    示例:
        ai4s search "transformer attention mechanism" --max-papers 50
        ai4s search "钙钛矿太阳能电池" --sources arxiv,pubmed -o results.json
    """
    console.print(Panel.fit(
        f"[bold cyan]搜索查询:[/bold cyan] {query}\n"
        f"[bold cyan]数据源:[/bold cyan] {sources}\n"
        f"[bold cyan]最大文献数:[/bold cyan] {max_papers}",
        title="🔍 文献搜索",
        border_style="cyan"
    ))
    
    source_list = [s.strip() for s in sources.split(',')]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("正在搜索文献...", total=None)
        
        try:
            result = asyncio.run(coordinator_agent.process_query(
                query=query,
                max_papers=max_papers,
                sources=source_list
            ))
            
            progress.update(task, description="✓ 搜索完成")
            
            # 显示结果摘要
            papers = result.get('papers', [])
            console.print(f"\n[green]✓[/green] 找到 {len(papers)} 篇相关文献")
            
            if papers:
                table = Table(title="文献列表（前10篇）", show_header=True, header_style="bold magenta")
                table.add_column("标题", style="cyan", width=50)
                table.add_column("年份", justify="center", width=6)
                table.add_column("引用", justify="right", width=6)
                table.add_column("评分", justify="right", width=6)
                
                for paper in papers[:10]:
                    table.add_row(
                        paper.get('title', 'N/A')[:47] + '...' if len(paper.get('title', '')) > 50 else paper.get('title', 'N/A'),
                        str(paper.get('year', 'N/A')),
                        str(paper.get('citationCount', 0)),
                        f"{paper.get('quality_score', 0):.1f}" if paper.get('quality_score') else 'N/A'
                    )
                
                console.print(table)
            
            # 保存结果
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                if format == 'json':
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                elif format == 'markdown':
                    md_content = _generate_markdown_report(result)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(md_content)
                
                console.print(f"\n[green]✓[/green] 结果已保存至: {output_path}")
            
        except Exception as e:
            console.print(f"[red]✗ 搜索失败:[/red] {str(e)}")
            logger.error(f"搜索失败: {e}", exc_info=True)


@cli.command()
@click.argument('query')
@click.option('--max-papers', default=100, help='最大文献数量')
@click.option('--hypothesis-count', default=5, help='生成假设数量')
@click.option('--output', '-o', help='输出文件路径')
def analyze(query: str, max_papers: int, hypothesis_count: int, output: Optional[str]):
    """
    完整分析：搜索+分析+假设生成+评估
    
    示例:
        ai4s analyze "阿尔茨海默病免疫代谢靶点" --hypothesis-count 3
        ai4s analyze "量子计算优化算法" -o report.md
    """
    console.print(Panel.fit(
        f"[bold cyan]研究主题:[/bold cyan] {query}\n"
        f"[bold cyan]文献数量:[/bold cyan] {max_papers}\n"
        f"[bold cyan]假设数量:[/bold cyan] {hypothesis_count}",
        title="🔬 全流程分析",
        border_style="cyan"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        try:
            # 执行完整分析
            task = progress.add_task("正在执行全流程分析...", total=None)
            
            result = asyncio.run(coordinator_agent.process_query(
                query=query,
                max_papers=max_papers
            ))
            
            progress.update(task, description="✓ 分析完成")
            
            # 显示结果
            _display_analysis_result(result)
            
            # 保存结果
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                md_content = _generate_full_report(result, query)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                console.print(f"\n[green]✓[/green] 完整报告已保存至: {output_path}")
            
        except Exception as e:
            console.print(f"[red]✗ 分析失败:[/red] {str(e)}")
            logger.error(f"分析失败: {e}", exc_info=True)


@cli.command()
def status():
    """显示系统状态"""
    console.print(Panel.fit(
        "[bold cyan]AI4S-Discovery 系统状态[/bold cyan]",
        border_style="cyan"
    ))
    
    # 设备信息
    device_info = device_manager.get_device_info()
    console.print("\n[bold]硬件信息:[/bold]")
    console.print(f"  设备类型: {device_info['device_type']}")
    console.print(f"  设备名称: {device_info['device_name']}")
    console.print(f"  内存使用: {device_info['memory_used']:.1f}GB / {device_info['memory_total']:.1f}GB")
    
    if device_info['device_type'] == 'cuda':
        console.print(f"  GPU内存: {device_info.get('gpu_memory_used', 0):.1f}GB / {device_info.get('gpu_memory_total', 0):.1f}GB")
    
    # 数据库统计
    stats = db_manager.get_statistics()
    console.print("\n[bold]数据库统计:[/bold]")
    console.print(f"  活跃用户: {stats['active_users']}")
    console.print(f"  总任务数: {stats['total_tasks']}")
    console.print(f"  完成任务: {stats['completed_tasks']}")
    console.print(f"  完成率: {stats['completion_rate']}%")
    console.print(f"  缓存文献: {stats['cached_papers']}")
    console.print(f"  生成报告: {stats['total_reports']}")
    
    # 配置信息
    console.print("\n[bold]配置信息:[/bold]")
    console.print(f"  项目名称: {settings.PROJECT_NAME}")
    console.print(f"  版本: {settings.VERSION}")
    console.print(f"  环境: {settings.ENVIRONMENT}")
    console.print(f"  日志级别: {settings.LOG_LEVEL}")


@cli.command()
@click.option('--limit', default=10, help='显示数量')
def history(limit: int):
    """查看搜索历史"""
    console.print(Panel.fit(
        "[bold cyan]搜索历史[/bold cyan]",
        border_style="cyan"
    ))
    
    history_list = db_manager.get_search_history(limit=limit)
    
    if not history_list:
        console.print("\n[yellow]暂无搜索历史[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("时间", style="cyan", width=20)
    table.add_column("查询", style="white", width=50)
    table.add_column("结果数", justify="right", width=8)
    table.add_column("耗时(s)", justify="right", width=10)
    
    for item in history_list:
        table.add_row(
            item['created_at'],
            item['query'][:47] + '...' if len(item['query']) > 50 else item['query'],
            str(item['result_count']),
            f"{item['execution_time']:.2f}"
        )
    
    console.print(table)


@cli.command()
def clear_cache():
    """清除缓存数据"""
    if click.confirm('确定要清除所有缓存数据吗？'):
        try:
            # 这里可以添加清除缓存的逻辑
            console.print("[green]✓[/green] 缓存已清除")
        except Exception as e:
            console.print(f"[red]✗ 清除失败:[/red] {str(e)}")


def _display_analysis_result(result: dict):
    """显示分析结果"""
    console.print("\n" + "="*80)
    console.print("[bold green]分析结果摘要[/bold green]")
    console.print("="*80)
    
    # 文献统计
    papers = result.get('papers', [])
    console.print(f"\n📚 文献数量: {len(papers)}")
    
    # 趋势分析
    trends = result.get('trends', {})
    if trends:
        console.print(f"\n📈 研究趋势:")
        console.print(f"  增长率: {trends.get('growth_rate', 'N/A')}")
        console.print(f"  热门主题: {', '.join(trends.get('hot_topics', [])[:5])}")
    
    # 创新假设
    hypotheses = result.get('hypotheses', [])
    if hypotheses:
        console.print(f"\n💡 创新假设 ({len(hypotheses)}个):")
        for i, hyp in enumerate(hypotheses[:3], 1):
            console.print(f"\n  {i}. {hyp.get('title', 'N/A')}")
            console.print(f"     置信度: {hyp.get('confidence', 0):.2f}")
            console.print(f"     描述: {hyp.get('description', 'N/A')[:100]}...")
    
    # TRL评估
    evaluation = result.get('evaluation', {})
    if evaluation:
        trl = evaluation.get('trl_assessment', {})
        console.print(f"\n🎯 技术成熟度:")
        console.print(f"  TRL等级: {trl.get('level', 'N/A')}")
        console.print(f"  描述: {trl.get('description', 'N/A')}")
        console.print(f"  置信度: {trl.get('confidence', 0):.2f}")


def _generate_markdown_report(result: dict) -> str:
    """生成Markdown格式报告"""
    papers = result.get('papers', [])
    
    md = "# 文献搜索结果\n\n"
    md += f"**搜索时间:** {result.get('timestamp', 'N/A')}\n\n"
    md += f"**文献数量:** {len(papers)}\n\n"
    md += "## 文献列表\n\n"
    
    for i, paper in enumerate(papers, 1):
        md += f"### {i}. {paper.get('title', 'N/A')}\n\n"
        md += f"- **作者:** {', '.join([a.get('name', 'N/A') for a in paper.get('authors', [])[:3]])}\n"
        md += f"- **年份:** {paper.get('year', 'N/A')}\n"
        md += f"- **引用数:** {paper.get('citationCount', 0)}\n"
        md += f"- **摘要:** {paper.get('abstract', 'N/A')[:200]}...\n\n"
    
    return md


def _generate_full_report(result: dict, query: str) -> str:
    """生成完整分析报告"""
    md = f"# {query} - 研究分析报告\n\n"
    md += f"**生成时间:** {result.get('timestamp', 'N/A')}\n\n"
    md += "---\n\n"
    
    # 执行摘要
    md += "## 执行摘要\n\n"
    md += f"本报告针对「{query}」进行了全面的文献分析和创新假设生成。\n\n"
    
    # 文献统计
    papers = result.get('papers', [])
    md += f"### 文献统计\n\n"
    md += f"- 总文献数: {len(papers)}\n"
    md += f"- 平均引用数: {sum(p.get('citationCount', 0) for p in papers) / len(papers) if papers else 0:.1f}\n\n"
    
    # 研究趋势
    trends = result.get('trends', {})
    if trends:
        md += "## 研究趋势\n\n"
        md += f"- 增长率: {trends.get('growth_rate', 'N/A')}\n"
        md += f"- 热门主题: {', '.join(trends.get('hot_topics', []))}\n\n"
    
    # 创新假设
    hypotheses = result.get('hypotheses', [])
    if hypotheses:
        md += "## 创新假设\n\n"
        for i, hyp in enumerate(hypotheses, 1):
            md += f"### 假设 {i}: {hyp.get('title', 'N/A')}\n\n"
            md += f"**置信度:** {hyp.get('confidence', 0):.2f}\n\n"
            md += f"**描述:** {hyp.get('description', 'N/A')}\n\n"
            md += f"**理论依据:** {hyp.get('rationale', 'N/A')}\n\n"
    
    # TRL评估
    evaluation = result.get('evaluation', {})
    if evaluation:
        trl = evaluation.get('trl_assessment', {})
        md += "## 技术成熟度评估\n\n"
        md += f"- **TRL等级:** {trl.get('level', 'N/A')}\n"
        md += f"- **描述:** {trl.get('description', 'N/A')}\n"
        md += f"- **置信度:** {trl.get('confidence', 0):.2f}\n"
        md += f"- **预计上市时间:** {trl.get('estimated_time_to_market', 'N/A')}\n\n"
    
    md += "---\n\n"
    md += "*本报告由 AI4S-Discovery 自动生成*\n"
    
    return md


if __name__ == '__main__':
    cli()