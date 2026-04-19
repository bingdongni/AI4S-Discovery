#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行界面（CLI）
提供交互式和非交互式的命令行操作
"""

import asyncio
import uuid
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown
from loguru import logger

from src.agents.coordinator_agent import coordinator, ResearchTask, TaskPriority
from src.utils.report_generator import ReportGenerator


class CLI:
    """命令行界面类"""
    
    def __init__(self):
        """初始化CLI"""
        self.console = Console()
        self.report_generator = ReportGenerator()
        logger.info("CLI初始化完成")
    
    def research(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        depth: str = "comprehensive",
        include_patents: bool = False,
        generate_hypotheses: bool = True,
        trl_assessment: bool = True,
    ) -> dict:
        """
        执行研究查询
        
        Args:
            query: 研究查询
            domains: 研究领域
            depth: 分析深度
            include_patents: 是否包含专利
            generate_hypotheses: 是否生成假设
            trl_assessment: 是否TRL评估
        
        Returns:
            dict: 研究结果
        """
        self.console.print(f"\n[bold cyan]🔬 开始研究任务[/bold cyan]")
        self.console.print(f"查询: [yellow]{query}[/yellow]")
        
        # 创建任务
        task_id = str(uuid.uuid4())
        task = ResearchTask(
            task_id=task_id,
            query=query,
            domains=domains,
            depth=depth,
            include_patents=include_patents,
            generate_hypotheses=generate_hypotheses,
            trl_assessment=trl_assessment,
            priority=TaskPriority.HIGH,
        )
        
        # 提交任务并等待完成
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task_progress = progress.add_task("执行中...", total=None)
            
            # 运行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(coordinator.submit_task(task))
            
            # 等待任务完成
            while task.status.value in ['pending', 'running']:
                loop.run_until_complete(asyncio.sleep(0.5))
                progress.update(
                    task_progress,
                    description=f"执行中... ({task.progress*100:.0f}%)"
                )
            
            loop.close()
        
        # 获取结果
        if task.status.value == 'completed':
            self.console.print("[bold green]✓ 任务完成[/bold green]\n")
            return task.results
        else:
            self.console.print(f"[bold red]✗ 任务失败: {task.errors}[/bold red]\n")
            return {}
    
    def print_result(self, result: dict):
        """
        打印研究结果
        
        Args:
            result: 研究结果
        """
        if not result:
            self.console.print("[yellow]没有结果[/yellow]")
            return
        
        # 1. 文献统计
        literature = result.get('literature', {})
        self.console.print(Panel.fit(
            f"[bold]文献搜索结果[/bold]\n\n"
            f"总计: {literature.get('total_papers', 0)} 篇\n"
            f"来源: {', '.join(f'{k}({v})' for k, v in literature.get('sources', {}).items())}",
            title="📚 文献统计",
            border_style="cyan"
        ))
        
        # 2. 分析结果
        analysis = result.get('analysis', {})
        if analysis:
            stats = analysis.get('statistics', {})
            
            self.console.print(Panel.fit(
                f"[bold]质量分析[/bold]\n\n"
                f"分析总数: {analysis.get('total_analyzed', 0)} 篇\n"
                f"高质量: {analysis.get('high_quality_count', 0)} 篇\n"
                f"质量阈值: {analysis.get('quality_threshold', 0)}\n"
                f"平均引用: {stats.get('avg_citations', 0):.1f}",
                title="📊 分析统计",
                border_style="green"
            ))
            
            # 关键词
            keywords = analysis.get('keywords', [])[:10]
            if keywords:
                table = Table(title="🔑 关键词（Top 10）", show_header=True)
                table.add_column("排名", style="cyan", width=6)
                table.add_column("关键词", style="yellow")
                table.add_column("TF-IDF", style="green", justify="right")
                table.add_column("频次", style="blue", justify="right")
                
                for idx, kw in enumerate(keywords, 1):
                    table.add_row(
                        str(idx),
                        kw.get('term', ''),
                        f"{kw.get('tfidf_score', 0):.4f}",
                        str(kw.get('frequency', 0))
                    )
                
                self.console.print(table)
            
            # 关键发现
            findings = analysis.get('key_findings', [])[:5]
            if findings:
                self.console.print("\n[bold cyan]💡 关键发现（Top 5）[/bold cyan]\n")
                for idx, finding in enumerate(findings, 1):
                    self.console.print(f"[bold]{idx}. {finding.get('title', '')}[/bold]")
                    self.console.print(f"   作者: {', '.join(finding.get('authors', [])[:3])}")
                    self.console.print(f"   年份: {finding.get('year', 'N/A')} | "
                                     f"质量分: {finding.get('quality_score', 0):.1f} | "
                                     f"引用: {finding.get('citations', 0)}")
                    self.console.print(f"   摘要: {finding.get('abstract', '')[:150]}...\n")
        
        # 3. 知识图谱
        graph = result.get('knowledge_graph', {})
        if graph:
            self.console.print(Panel.fit(
                f"[bold]图谱构建[/bold]\n\n"
                f"节点数: {graph.get('nodes', 0)}\n"
                f"边数: {graph.get('edges', 0)}\n"
                f"聚类数: {len(graph.get('clusters', []))}",
                title="🕸️ 知识图谱",
                border_style="magenta"
            ))
        
        # 4. TRL评估
        trl = result.get('trl_assessment', {})
        if trl and trl.get('level'):
            self.console.print(Panel.fit(
                f"[bold]技术成熟度评估[/bold]\n\n"
                f"TRL等级: {trl.get('level', 0)}\n"
                f"置信度: {trl.get('confidence', 0):.2%}",
                title="📈 TRL评估",
                border_style="yellow"
            ))
        
        # 5. 创新假设
        hypotheses = result.get('hypotheses', [])
        if hypotheses:
            self.console.print("\n[bold cyan]💭 创新假设[/bold cyan]\n")
            for idx, hyp in enumerate(hypotheses, 1):
                self.console.print(f"{idx}. {hyp}")
    
    def export_report(self, result: dict, output_path: str, format: str = 'pdf'):
        """
        导出报告
        
        Args:
            result: 研究结果
            output_path: 输出路径
            format: 报告格式
        """
        self.console.print(f"\n[cyan]正在生成{format.upper()}报告...[/cyan]")
        
        try:
            self.report_generator.generate(
                result=result,
                output_path=output_path,
                format=format
            )
            self.console.print(f"[green]✓ 报告已保存至: {output_path}[/green]")
        except Exception as e:
            self.console.print(f"[red]✗ 报告生成失败: {e}[/red]")
    
    def interactive_mode(self):
        """交互式模式"""
        self.console.print(Panel.fit(
            "[bold cyan]AI4S-Discovery 交互式命令行[/bold cyan]\n\n"
            "输入研究查询开始，输入 'exit' 或 'quit' 退出",
            border_style="cyan"
        ))
        
        while True:
            try:
                # 获取查询
                query = self.console.input("\n[bold yellow]研究查询>[/bold yellow] ")
                
                if query.lower() in ['exit', 'quit', 'q']:
                    self.console.print("[cyan]再见！[/cyan]")
                    break
                
                if not query.strip():
                    continue
                
                # 询问参数
                depth = self.console.input(
                    "[dim]分析深度 (quick/standard/comprehensive) [comprehensive]:[/dim] "
                ).strip() or "comprehensive"
                
                include_patents = self.console.input(
                    "[dim]包含专利? (y/n) [n]:[/dim] "
                ).strip().lower() == 'y'
                
                # 执行研究
                result = self.research(
                    query=query,
                    depth=depth,
                    include_patents=include_patents,
                    generate_hypotheses=True,
                    trl_assessment=True,
                )
                
                # 显示结果
                self.print_result(result)
                
                # 询问是否导出
                export = self.console.input(
                    "\n[dim]是否导出报告? (y/n) [n]:[/dim] "
                ).strip().lower()
                
                if export == 'y':
                    output_path = self.console.input(
                        "[dim]输出路径:[/dim] "
                    ).strip()
                    
                    format = self.console.input(
                        "[dim]格式 (pdf/docx/html/markdown) [pdf]:[/dim] "
                    ).strip() or "pdf"
                    
                    if output_path:
                        self.export_report(result, output_path, format)
                
            except KeyboardInterrupt:
                self.console.print("\n[cyan]再见！[/cyan]")
                break
            except Exception as e:
                self.console.print(f"[red]错误: {e}[/red]")
                logger.exception("交互式模式错误")
