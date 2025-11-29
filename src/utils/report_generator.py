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
        
        # 3. 知识图谱分析
        graph = result.get('knowledge_graph', {})
        if graph:
            lines.append("## 🕸️ 知识图谱分析\n")
            
            # 基本统计
            lines.append("### 图谱统计")
            lines.append(f"- **节点数**: {graph.get('node_count', 0)}")
            lines.append(f"- **边数**: {graph.get('edge_count', 0)}")
            lines.append(f"- **平均度**: {graph.get('avg_degree', 0):.2f}")
            lines.append(f"- **图密度**: {graph.get('density', 0):.4f}")
            lines.append("")
            
            # 社区结构
            communities = graph.get('communities', [])
            if communities:
                lines.append("### 研究社区")
                lines.append(f"发现 {len(communities)} 个研究社区：\n")
                for idx, comm in enumerate(communities[:5], 1):
                    lines.append(f"#### 社区 {idx}")
                    lines.append(f"- 规模: {comm.get('size', 0)} 个节点")
                    lines.append(f"- 核心主题: {', '.join(comm.get('topics', [])[:5])}")
                    lines.append(f"- 代表文献: {comm.get('representative_papers', ['N/A'])[0]}")
                    lines.append("")
            
            # 关键节点
            key_nodes = graph.get('key_nodes', [])
            if key_nodes:
                lines.append("### 关键节点（Top 10）\n")
                lines.append("| 排名 | 文献 | 度中心性 | 介数中心性 | PageRank |")
                lines.append("|------|------|----------|------------|----------|")
                for idx, node in enumerate(key_nodes[:10], 1):
                    lines.append(f"| {idx} | {node.get('title', '')[:50]}... | "
                               f"{node.get('degree_centrality', 0):.4f} | "
                               f"{node.get('betweenness_centrality', 0):.4f} | "
                               f"{node.get('pagerank', 0):.4f} |")
                lines.append("")
        
        # 4. TRL技术成熟度评估
        trl = result.get('trl_assessment', {})
        if trl:
            lines.append("## 📊 技术成熟度评估（TRL）\n")
            
            # 总体评估
            lines.append("### 总体评估")
            lines.append(f"- **TRL等级**: {trl.get('trl_level', 'N/A')}")
            lines.append(f"- **置信度**: {trl.get('confidence', 0):.2%}")
            lines.append(f"- **评估方法**: {trl.get('method', 'N/A')}")
            lines.append("")
            
            # TRL分布
            distribution = trl.get('distribution', {})
            if distribution:
                lines.append("### TRL等级分布\n")
                lines.append("| TRL等级 | 文献数量 | 占比 |")
                lines.append("|---------|----------|------|")
                for level in range(1, 10):
                    count = distribution.get(f'TRL{level}', 0)
                    if count > 0:
                        percentage = count / trl.get('total_papers', 1) * 100
                        lines.append(f"| TRL {level} | {count} | {percentage:.1f}% |")
                lines.append("")
            
            # 技术可行性
            feasibility = trl.get('feasibility', {})
            if feasibility:
                lines.append("### 技术可行性分析")
                lines.append(f"- **技术成熟度**: {feasibility.get('maturity', 'N/A')}")
                lines.append(f"- **实施难度**: {feasibility.get('difficulty', 'N/A')}")
                lines.append(f"- **资源需求**: {feasibility.get('resource_requirement', 'N/A')}")
                lines.append(f"- **时间估计**: {feasibility.get('time_estimate', 'N/A')}")
                lines.append("")
            
            # 关键里程碑
            milestones = trl.get('milestones', [])
            if milestones:
                lines.append("### 关键里程碑")
                for milestone in milestones:
                    lines.append(f"- **{milestone.get('stage', '')}**: {milestone.get('description', '')}")
                lines.append("")
        
        # 5. 创新假设生成
        innovations = result.get('innovations', {})
        hypotheses = innovations.get('hypotheses', []) if innovations else []
        if hypotheses:
            lines.append("## 💡 创新假设\n")
            
            for idx, hyp in enumerate(hypotheses, 1):
                lines.append(f"### 假设 {idx}: {hyp.get('title', '')}\n")
                lines.append(f"**ID**: {hyp.get('id', '')}")
                lines.append(f"**置信度**: {hyp.get('confidence', 0):.2%}\n")
                
                lines.append("#### 描述")
                lines.append(f"{hyp.get('description', '')}\n")
                
                lines.append("#### 理论依据")
                lines.append(f"{hyp.get('rationale', '')}\n")
                
                # 可行性
                feasibility = hyp.get('feasibility', {})
                lines.append("#### 可行性评估")
                lines.append(f"- **技术可行性**: {feasibility.get('technical', 'N/A')}")
                lines.append(f"- **资源可行性**: {feasibility.get('resource', 'N/A')}")
                lines.append(f"- **时间可行性**: {feasibility.get('time', 'N/A')}")
                lines.append("")
                
                # 所需资源
                resources = hyp.get('required_resources', {})
                if resources:
                    lines.append("#### 所需资源")
                    lines.append(f"- **资金**: {resources.get('funding', 'N/A')}")
                    lines.append(f"- **团队**: {resources.get('team_size', 'N/A')}")
                    lines.append(f"- **周期**: {resources.get('duration', 'N/A')}")
                    lines.append("")
                
                # 支撑文献
                supporting = hyp.get('supporting_papers', [])
                if supporting:
                    lines.append("#### 支撑文献")
                    for paper in supporting[:3]:
                        lines.append(f"- {paper}")
                    lines.append("")
        
        # 6. 反事实推理
        counterfactuals = innovations.get('counterfactual_reasoning', []) if innovations else []
        if counterfactuals:
            lines.append("## 🔮 反事实推理分析\n")
            
            for cf_group in counterfactuals:
                hyp_id = cf_group.get('hypothesis_id', '')
                scenarios = cf_group.get('scenarios', [])
                
                if scenarios:
                    lines.append(f"### 针对假设 {hyp_id}\n")
                    
                    for idx, scenario in enumerate(scenarios, 1):
                        lines.append(f"#### 场景 {idx}: {scenario.get('scenario', '')}\n")
                        
                        lines.append(f"**条件变化**: {scenario.get('condition_change', '')}\n")
                        lines.append(f"**预期结果**: {scenario.get('expected_outcome', '')}\n")
                        lines.append(f"**成功概率**: {scenario.get('success_probability', 0):.2%}\n")
                        
                        risks = scenario.get('risks', [])
                        if risks:
                            lines.append("**潜在风险**:")
                            for risk in risks:
                                lines.append(f"- {risk}")
                            lines.append("")
                        
                        adjustments = scenario.get('required_adjustments', [])
                        if adjustments:
                            lines.append("**所需调整**:")
                            for adj in adjustments:
                                lines.append(f"- {adj}")
                            lines.append("")
                        
                        lines.append(f"**时间影响**: {scenario.get('impact_on_timeline', 'N/A')}")
                        lines.append(f"**资源影响**: {scenario.get('impact_on_resources', 'N/A')}\n")
        
        # 7. 跨域知识迁移
        transfers = innovations.get('cross_domain_transfers', []) if innovations else []
        if transfers:
            lines.append("## 🔄 跨域知识迁移推荐\n")
            
            for idx, transfer in enumerate(transfers, 1):
                lines.append(f"### 迁移方案 {idx}\n")
                lines.append(f"**源领域**: {transfer.get('source_domain', '')}")
                lines.append(f"**目标领域**: {transfer.get('target_domain', '')}")
                lines.append(f"**相似度**: {transfer.get('similarity_score', 0):.2%}")
                lines.append(f"**成功概率**: {transfer.get('success_probability', 0):.2%}\n")
                
                lines.append(f"**源方法**: {transfer.get('source_method', '')}")
                lines.append(f"**目标应用**: {transfer.get('target_application', '')}\n")
                
                lines.append(f"**预期收益**: {transfer.get('expected_benefit', '')}\n")
                
                challenges = transfer.get('challenges', [])
                if challenges:
                    lines.append("**挑战**:")
                    for challenge in challenges:
                        lines.append(f"- {challenge}")
                    lines.append("")
                
                steps = transfer.get('implementation_steps', [])
                if steps:
                    lines.append("**实施步骤**:")
                    for step in steps:
                        lines.append(f"{step}")
                    lines.append("")
        
        # 页脚
        lines.append("\n---")
        lines.append("\n*本报告由 AI4S-Discovery 自动生成*")
        
        return "\n".join(lines)


# 创建全局报告生成器实例
report_generator = ReportGenerator()
