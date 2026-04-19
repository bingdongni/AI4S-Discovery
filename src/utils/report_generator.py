#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告生成器
支持多种格式：PDF、DOCX、HTML、Markdown
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from jinja2 import Template
from loguru import logger

from src.core.config import settings


class ReportGenerator:
    """报告生成器"""

    def __init__(self):
        """初始化报告生成器"""
        self.template_dir = Path(settings.TEMPLATE_DIR)
        self.output_dir = Path(settings.REPORT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("报告生成器初始化完成")

    def generate(
        self,
        result: Dict[str, Any],
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

        # 确保输出目录存在
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

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

    def _generate_markdown(self, result: Dict[str, Any], output_path: str):
        """生成Markdown报告"""
        content = self._build_markdown_content(result)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.success(f"Markdown报告已生成: {output_path}")

    def _generate_html(self, result: Dict[str, Any], output_path: str):
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
        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
        code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
    </style>
</head>
<body>
    <div style="white-space: pre-wrap; word-wrap: break-word;">{{ content }}</div>
</body>
</html>
        """

        template = Template(html_template)
        html_content = template.render(content=markdown_content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.success(f"HTML报告已生成: {output_path}")

    def _build_markdown_content(self, result: Dict[str, Any]) -> str:
        """构建Markdown内容"""
        lines = []

        # 标题
        lines.append("# AI4S-Discovery 研究报告\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("---\n")

        # 1. 文献统计
        literature = result.get('literature', {})
        lines.append("## 📚 文献统计\n")
        lines.append(f"- **总计**: {literature.get('total_papers', 0)} 篇")

        sources = literature.get('sources', {})
        if sources:
            lines.append(f"- **来源分布**:")
            for source, count in sources.items():
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

            if stats:
                if 'avg_citations' in stats:
                    lines.append(f"- 平均引用数: {stats.get('avg_citations', 0):.1f}")
                if 'total_citations' in stats:
                    lines.append(f"- 总引用数: {stats.get('total_citations', 0)}")
            lines.append("")

            # 关键词
            keywords = analysis.get('keywords', [])
            if keywords and len(keywords) > 0:
                lines.append("### 🔑 关键词（Top 20）\n")
                lines.append("| 排名 | 关键词 | TF-IDF | 频次 |")
                lines.append("|------|--------|--------|------|")
                for idx, kw in enumerate(keywords[:20], 1):
                    if isinstance(kw, dict):
                        lines.append(f"| {idx} | {kw.get('term', '')} | {kw.get('tfidf_score', 0):.4f} | {kw.get('frequency', 0)} |")
                    else:
                        lines.append(f"| {idx} | {kw} | - | - |")
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
                    if isinstance(finding, dict):
                        title = finding.get('title', 'Unknown')
                        authors_list = finding.get('authors', [])
                        if isinstance(authors_list, list):
                            authors_str = ', '.join(authors_list[:3])
                        else:
                            authors_str = str(authors_list)
                        lines.append(f"#### {idx}. {title}")
                        lines.append(f"**作者**: {authors_str}")
                        year = finding.get('year', 'N/A')
                        score = finding.get('quality_score', 0)
                        citations = finding.get('citations', 0)
                        lines.append(f"**年份**: {year} | **质量分**: {score:.1f} | **引用**: {citations}")
                        abstract = finding.get('abstract', '')
                        if abstract:
                            lines.append(f"\n**摘要**: {abstract[:300]}...\n")
                lines.append("")

        # 3. 知识图谱分析
        graph = result.get('knowledge_graph', {})
        if graph:
            lines.append("## 🕸️ 知识图谱分析\n")

            # 基本统计
            stats = graph.get('statistics', {})

            # 兼容不同的字段名
            nodes = graph.get('nodes', graph.get('node_count', 0))
            edges = graph.get('edges', graph.get('edge_count', 0))

            lines.append("### 图谱统计")
            lines.append(f"- **节点数**: {nodes}")
            lines.append(f"- **边数**: {edges}")

            if stats:
                avg_degree = stats.get('avg_degree', 0)
                density = stats.get('density', 0)
                lines.append(f"- **平均度**: {avg_degree:.2f}")
                lines.append(f"- **图密度**: {density:.4f}")
                lines.append(f"- **连通分量**: {stats.get('connected_components', 0)}")
            lines.append("")

            # 社区结构
            clusters = graph.get('clusters', graph.get('communities', []))
            if clusters and len(clusters) > 0:
                lines.append(f"### 研究社区")
                lines.append(f"发现 {len(clusters)} 个研究社区：\n")
                for idx, cluster in enumerate(clusters[:5], 1):
                    if isinstance(cluster, dict):
                        size = cluster.get('size', 0)
                        theme = cluster.get('theme', cluster.get('topics', ['未知']))
                        if isinstance(theme, list):
                            theme_str = ', '.join(theme[:5])
                        else:
                            theme_str = str(theme)
                        lines.append(f"#### 社区 {idx}")
                        lines.append(f"- 规模: {size} 个节点")
                        lines.append(f"- 核心主题: {theme_str}")
                        lines.append("")
                    else:
                        lines.append(f"#### 社区 {idx}: {cluster}")

            # 关键节点
            key_nodes = graph.get('key_nodes', [])
            if key_nodes and len(key_nodes) > 0:
                lines.append("### 关键节点（Top 10）\n")
                lines.append("| 排名 | 文献 | 年份 | 重要性 | 度 | 引用 |")
                lines.append("|------|------|------|--------|----|------|")
                for idx, node in enumerate(key_nodes[:10], 1):
                    if isinstance(node, dict):
                        title = node.get('title', node.get('node_id', 'Unknown'))[:40]
                        year = node.get('year', 'N/A')
                        score = node.get('importance_score', 0)
                        degree = node.get('degree', 0)
                        citations = node.get('citation_count', 0)
                        lines.append(f"| {idx} | {title}... | {year} | {score:.4f} | {degree} | {citations} |")
                lines.append("")

            # 研究演进路径
            evolution_paths = graph.get('evolution_paths', [])
            if evolution_paths and len(evolution_paths) > 0:
                lines.append("### 研究演进路径\n")
                for idx, path in enumerate(evolution_paths[:3], 1):
                    if isinstance(path, dict):
                        length = path.get('length', 0)
                        start_year = path.get('start_year', 'N/A')
                        end_year = path.get('end_year', 'N/A')
                        lines.append(f"#### 路径 {idx}")
                        lines.append(f"- 路径长度: {length} 步")
                        lines.append(f"- 时间跨度: {start_year} → {end_year}")
                        lines.append("")

        # 4. TRL技术成熟度评估
        trl = result.get('trl_assessment', {})
        if trl:
            lines.append("## 📊 技术成熟度评估（TRL）\n")

            # 总体评估
            lines.append("### 总体评估")
            level = trl.get('level', trl.get('trl_level', 0))
            confidence = trl.get('confidence', 0)
            description = trl.get('level_description', '')
            lines.append(f"- **TRL等级**: {level}")
            lines.append(f"- **等级描述**: {description}")
            lines.append(f"- **置信度**: {confidence:.2%}")
            lines.append("")

            # TRL分布
            distribution = trl.get('distribution', {})
            if distribution:
                lines.append("### TRL等级分布\n")
                lines.append("| TRL等级 | 描述 | 得分 |")
                lines.append("|---------|------|------|")
                for level in range(1, 10):
                    if str(level) in distribution:
                        dist = distribution[str(level)]
                        desc = dist.get('description', '')[:30]
                        score = dist.get('score', 0)
                        lines.append(f"| {level} | {desc}... | {score:.4f} |")
                    elif level in distribution:
                        dist = distribution[level]
                        desc = dist.get('description', '')[:30]
                        score = dist.get('score', 0)
                        lines.append(f"| {level} | {desc}... | {score:.4f} |")
                lines.append("")

            # 证据
            evidence = trl.get('evidence', [])
            if evidence and len(evidence) > 0:
                lines.append("### 支持证据\n")
                for idx, ev in enumerate(evidence[:5], 1):
                    if isinstance(ev, dict):
                        title = ev.get('title', 'Unknown')[:50]
                        year = ev.get('year', 'N/A')
                        score = ev.get('quality_score', 0)
                        keywords = ev.get('matched_keywords', [])
                        lines.append(f"- [{idx}] {title}... ({year}) - 质量分: {score:.1f}")
                        if keywords:
                            lines.append(f"  - 关键词: {', '.join(keywords[:5])}")
                lines.append("")

            # TRL趋势
            trend = trl.get('trend', {})
            if trend:
                trend_value = trend.get('trend', 'unknown')
                current_trl = trend.get('current_trl', 0)
                lines.append(f"### TRL趋势")
                lines.append(f"- **趋势**: {trend_value}")
                lines.append(f"- **当前TRL**: {current_trl}")
                lines.append("")

        # 可行性评估
        feasibility = result.get('feasibility', {})
        if feasibility:
            lines.append("### 技术可行性")
            lines.append(f"- **可行性**: {feasibility.get('feasibility', 'unknown')}")
            lines.append(f"- **建议**: {feasibility.get('recommendation', 'N/A')}")
            lines.append(f"- **风险等级**: {feasibility.get('risk_level', 'unknown')}")
            lines.append("")

        # 5. 创新假设生成
        innovations = result.get('innovations', {})
        hypotheses = innovations.get('hypotheses', []) if innovations else []

        if hypotheses and len(hypotheses) > 0:
            lines.append("## 💡 创新假设\n")

            for idx, hyp in enumerate(hypotheses, 1):
                if isinstance(hyp, dict):
                    lines.append(f"### 假设 {idx}: {hyp.get('title', 'Unknown')}\n")
                    lines.append(f"**ID**: {hyp.get('id', '')}")

                    confidence = hyp.get('confidence', 0)
                    lines.append(f"**置信度**: {confidence:.2%}\n")

                    description = hyp.get('description', '')
                    if description:
                        lines.append(f"#### 描述")
                        lines.append(f"{description}\n")

                    rationale = hyp.get('rationale', '')
                    if rationale:
                        lines.append(f"#### 理论依据")
                        lines.append(f"{rationale}\n")

                    # 可行性
                    feasibility_hyp = hyp.get('feasibility', {})
                    if feasibility_hyp:
                        lines.append("#### 可行性评估")
                        technical = feasibility_hyp.get('technical', 'N/A')
                        resource = feasibility_hyp.get('resource', 'N/A')
                        time_feasibility = feasibility_hyp.get('time', 'N/A')
                        lines.append(f"- **技术可行性**: {technical}")
                        lines.append(f"- **资源可行性**: {resource}")
                        lines.append(f"- **时间可行性**: {time_feasibility}")
                        lines.append("")

                    # 预期影响
                    impact = hyp.get('expected_impact', '')
                    if impact:
                        lines.append(f"#### 预期影响: {impact}\n")

                    # 所需资源
                    resources = hyp.get('required_resources', {})
                    if resources and isinstance(resources, dict):
                        lines.append("#### 所需资源")
                        funding = resources.get('funding', 'N/A')
                        team = resources.get('team_size', 'N/A')
                        duration = resources.get('duration', 'N/A')
                        lines.append(f"- **资金**: {funding}")
                        lines.append(f"- **团队**: {team}")
                        lines.append(f"- **周期**: {duration}")
                        lines.append("")

                    # 支撑文献
                    supporting = hyp.get('supporting_papers', [])
                    if supporting and len(supporting) > 0:
                        lines.append("#### 支撑文献")
                        for paper in supporting[:3]:
                            lines.append(f"- {paper}")
                        lines.append("")

        # 6. 反事实推理
        counterfactuals = innovations.get('counterfactual_reasoning', []) if innovations else []

        if counterfactuals and len(counterfactuals) > 0:
            lines.append("## 🔮 反事实推理分析\n")

            for cf_group in counterfactuals:
                if isinstance(cf_group, dict):
                    hyp_id = cf_group.get('hypothesis_id', '')
                    scenarios = cf_group.get('scenarios', [])

                    if scenarios and len(scenarios) > 0:
                        lines.append(f"### 针对假设 {hyp_id}\n")

                        for idx, scenario in enumerate(scenarios, 1):
                            if isinstance(scenario, dict):
                                scenario_name = scenario.get('scenario', f'场景 {idx}')
                                lines.append(f"#### 场景 {idx}: {scenario_name}\n")

                                condition = scenario.get('condition_change', '')
                                if condition:
                                    lines.append(f"**条件变化**: {condition}\n")

                                outcome = scenario.get('expected_outcome', '')
                                if outcome:
                                    lines.append(f"**预期结果**: {outcome}\n")

                                prob = scenario.get('success_probability', 0)
                                lines.append(f"**成功概率**: {prob:.2%}\n")

                                risks = scenario.get('risks', [])
                                if risks and len(risks) > 0:
                                    lines.append("**潜在风险**:")
                                    for risk in risks:
                                        lines.append(f"- {risk}")
                                    lines.append("")

                                adjustments = scenario.get('required_adjustments', [])
                                if adjustments and len(adjustments) > 0:
                                    lines.append("**所需调整**:")
                                    for adj in adjustments:
                                        lines.append(f"- {adj}")
                                    lines.append("")

        # 7. 跨域知识迁移
        transfers = innovations.get('cross_domain_transfers', []) if innovations else []

        if transfers and len(transfers) > 0:
            lines.append("## 🔄 跨域知识迁移推荐\n")

            for idx, transfer in enumerate(transfers, 1):
                if isinstance(transfer, dict):
                    lines.append(f"### 迁移方案 {idx}\n")

                    source_domain = transfer.get('source_domain', 'N/A')
                    target_domain = transfer.get('target_domain', 'N/A')
                    lines.append(f"**源领域 → 目标领域**: {source_domain} → {target_domain}")

                    similarity = transfer.get('similarity_score', 0)
                    success_prob = transfer.get('success_probability', 0)
                    lines.append(f"**相似度**: {similarity:.2%} | **成功概率**: {success_prob:.2%}\n")

                    source_method = transfer.get('source_method', '')
                    target_app = transfer.get('target_application', '')
                    if source_method:
                        lines.append(f"**源方法**: {source_method}")
                    if target_app:
                        lines.append(f"**目标应用**: {target_app}")

                    benefit = transfer.get('expected_benefit', '')
                    if benefit:
                        lines.append(f"\n**预期收益**: {benefit}\n")

                    challenges = transfer.get('challenges', [])
                    if challenges and len(challenges) > 0:
                        lines.append("**挑战**:")
                        for challenge in challenges:
                            lines.append(f"- {challenge}")
                        lines.append("")

                    steps = transfer.get('implementation_steps', [])
                    if steps and len(steps) > 0:
                        lines.append("**实施步骤**:")
                        for step in steps:
                            lines.append(f"- {step}")
                        lines.append("")

        # 8. 报告信息
        report_info = result.get('report', {})
        if report_info:
            lines.append("## 📋 报告信息\n")
            generated_at = report_info.get('generated_at', report_info.get('created_at', datetime.now().isoformat()))
            lines.append(f"- **生成时间**: {generated_at}")

            md_path = report_info.get('markdown_path', '')
            html_path = report_info.get('html_path', '')
            if md_path:
                lines.append(f"- **Markdown路径**: {md_path}")
            if html_path:
                lines.append(f"- **HTML路径**: {html_path}")
            lines.append("")

        # 页脚
        lines.append("\n---")
        lines.append("\n*本报告由 AI4S-Discovery 自动生成*")
        lines.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)


# 创建全局报告生成器实例
report_generator = ReportGenerator()
