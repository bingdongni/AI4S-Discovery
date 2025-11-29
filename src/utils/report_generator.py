#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告生成器
支持多种格式：PDF、DOCX、HTML、Markdown
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict
from jinja2 import Template
from loguru import logger

from src.core.config import settings


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.template_dir = Path(settings.REPORT_TEMPLATE_PATH)
        self.output_dir = Path(settings.REPORT_OUTPUT_PATH)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("报告生成器初始化完成")
    
    def generate(
        self,
        result: Dict,
        output_path: str,
        format: str = 'markdown',
        template: str = 'default',
    ):
        """
        生成报告
        
        Args:
            result: 研究结果
            output_path: 输出路径
            format: 报告格式
            template: 模板名称
        """
        logger.info(f"生成{format}报告: {output_path}")
        
        if format == 'markdown':
            self._generate_markdown(result, output_path)
        elif format == 'html':
            self._generate_html(result, output_path)
        elif format == 'pdf':
            # PDF生成需要先生成HTML再转换
            html_path = output_path.replace('.pdf', '.html')
            self._generate_html(result, html_path)
            logger.info(f"PDF生成需要额外工具，已生成HTML版本: {html_path}")
        elif format == 'docx':
            logger.warning("DOCX格式暂未实现，生成Markdown代替")
            self._generate_markdown(result, output_path.replace('.docx', '.md'))
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _generate_markdown(self, result: Dict, output_path: str):
        """生成Markdown报告"""
        content = self._build_markdown_content(result)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.success(f"Markdown报告已生成: {output_path}")
    
    def _generate_html(self, result: Dict, output_path: str):
        """生成HTML报告"""
        markdown_content = self._build_markdown_content(result)
        
        # 简单的HTML模板
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AI4S-Discovery 研究报告</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; border-bottom: 2px solid #95a5a6; padding-bottom: 8px; margin-top: 30px; }
        h3 { color: #7f8c8d; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .stat-box { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .keyword { display: inline-block; background: #3498db; color: white; padding: 5px 10px; margin: 5px; border-radius: 3px; }
    </style>
</head>
<body>
    <pre>{{ content }}</pre>
</body>
</html>
        """
        
        template = Template(html_template)
        html_content = template.render(content=markdown_content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.success(f"HTML报告已生成: {output_path}")
    
    def _build_markdown_content(self, result: Dict) -> str:
        """构建Markdown内容"""
        lines = []
        
        # 标题
        lines.append("# AI4S-Discovery 研究报告")
        lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("---\n")
        
        # 1. 文献统计
        literature = result.get('literature', {})
        lines.append("## 📚 文献统计\n")
        lines.append(f"- **总计**: {literature.get('total_papers', 0)} 篇")
        lines.append(f"- **来源分布**:")
        for source, count in literature.get('sources', {}).items():
            lines.append(f"  - {source}: {count} 篇")
        lines.append("")
        
        # 2. 分析结果
        analysis = result.get('analysis', {})
        if analysis:
            lines.append("## 📊 分析结果\n")
            
            stats = analysis.get('statistics', {})
            lines.append("### 质量分析")
            lines.append(f"- 分析总数: {analysis.get('total_analyzed', 0)} 篇")
            lines.append(f"- 高质量文献: {analysis.get('high_quality_count', 0)} 篇")
            lines.append(f"- 质量阈值: {analysis.get('quality_threshold', 0)}")
            lines.append(f"- 平均引用数: {stats.get('avg_citations', 0):.1f}")
            lines.append("")
            
            # 关键词
            keywords = analysis.get('keywords', [])[:20]
            if keywords:
                lines.append("### 🔑 关键词（Top 20）\n")
                lines.append("| 排名 | 关键词 | TF-IDF | 频次 |")
                lines.append("|------|--------|--------|------|")
                for idx, kw in enumerate(keywords, 1):
                    lines.append(f"| {idx} | {kw.get('term', '')} | {kw.get('tfidf_score', 0):.4f} | {kw.get('frequency', 0)} |")
                lines.append("")
            
            # 趋势分析
            trends = analysis.get('trends', {})
            if trends:
                lines.append("### 📈 研究趋势\n")
                
                # 年度分布
                yearly = trends.get('yearly_distribution', {})
                if yearly:
                    lines.append("#### 年度分布")
                    for year, count in sorted(yearly.items()):
                        lines.append(f"- {year}: {count} 篇")
                    lines.append("")
                
                # 高产作者
                authors = trends.get('author_distribution', {})
                if authors:
                    lines.append("#### 高产作者（Top 10）")
                    for author, count in list(authors.items())[:10]:
                        lines.append(f"- {author}: {count} 篇")
                    lines.append("")
            
            # 关键发现
            findings = analysis.get('key_findings', [])
            if findings:
                lines.append("### 💡 关键发现\n")
                for idx, finding in enumerate(findings, 1):
                    lines.append(f"#### {idx}. {finding.get('title', '')}")
                    lines.append(f"**作者**: {', '.join(finding.get('authors', [])[:3])}")
                    lines.append(f"**年份**: {finding.get('year', 'N/A')} | "
                               f"**质量分**: {finding.get('quality_score', 0):.1f} | "
                               f"**引用**: {finding.get('citations', 0)}")
                    lines.append(f"\n**摘要**: {finding.get('abstract', '')}\n")
        
        # 3. 知识图谱
        graph = result.get('knowledge_graph', {})
        if graph:
            lines.append("## 🕸️ 知识图谱\n")
            lines.append(f"- 节点数: {graph.get('nodes', 0)}")
            lines.append(f"- 边数: {graph.get('edges', 0)}")
            lines.append(f"- 聚类数: {len(graph.get('clusters', []))}")
            lines.append("")
        
        # 4. TRL评估
        trl = result.get('trl_assessment', {})
        if trl and trl.get('level'):
            lines.append("## 📈 技术成熟度评估\n")
            lines.append(f"- **TRL等级**: {trl.get('level', 0)}")
            lines.append(f"- **置信度**: {trl.get('confidence', 0):.2%}")
            lines.append("")
        
        # 5. 创新假设
        hypotheses = result.get('hypotheses', [])
        if hypotheses:
            lines.append("## 💭 创新假设\n")
            for idx, hyp in enumerate(hypotheses, 1):
                lines.append(f"{idx}. {hyp}")
            lines.append("")
        
        # 页脚
        lines.append("\n---")
        lines.append("\n*本报告由 AI4S-Discovery 自动生成*")
        
        return "\n".join(lines)


# 创建全局报告生成器实例
report_generator = ReportGenerator()
