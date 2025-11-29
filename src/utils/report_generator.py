#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告模板引擎
支持多种报告类型的自动生成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from loguru import logger
import markdown
from weasyprint import HTML
import json

from src.core.config import settings


class ReportGenerator:
    """报告生成器"""
    
    # 预定义报告模板
    TEMPLATES = {
        'research_analysis': """# {{ title }}

**生成时间**: {{ timestamp }}  
**研究主题**: {{ query }}

---

## 执行摘要

{{ summary }}

## 文献统计

- **总文献数**: {{ paper_count }}
- **平均引用数**: {{ avg_citations }}
- **年份范围**: {{ year_range }}
- **主要来源**: {{ sources }}

## 研究趋势

{% if trends %}
### 发展趋势
{{ trends.description }}

### 热门主题
{% for topic in trends.hot_topics %}
- {{ topic }}
{% endfor %}

### 增长率
{{ trends.growth_rate }}
{% endif %}

## 创新假设

{% for hypothesis in hypotheses %}
### 假设 {{ loop.index }}: {{ hypothesis.title }}

**置信度**: {{ "%.2f"|format(hypothesis.confidence) }}  
**预期影响**: {{ hypothesis.expected_impact }}

#### 描述
{{ hypothesis.description }}

#### 理论依据
{{ hypothesis.rationale }}

#### 所需资源
- **资金**: {{ hypothesis.required_resources.funding }}
- **团队**: {{ hypothesis.required_resources.team_size }}
- **时间**: {{ hypothesis.timeline }}

#### 风险评估
{% for risk in hypothesis.risks %}
- **{{ risk.type }}**: {{ risk.description }} (严重程度: {{ risk.severity }})
{% endfor %}

---
{% endfor %}

## 技术成熟度评估

{% if trl_assessment %}
- **TRL等级**: {{ trl_assessment.level }}
- **描述**: {{ trl_assessment.description }}
- **置信度**: {{ "%.2f"|format(trl_assessment.confidence) }}
- **预计上市时间**: {{ trl_assessment.estimated_time_to_market }}

### 下一步建议
{% for step in trl_assessment.next_steps %}
- {{ step }}
{% endfor %}
{% endif %}

## 重点文献

{% for paper in top_papers[:10] %}
### {{ loop.index }}. {{ paper.title }}

- **作者**: {{ paper.authors|join(', ') }}
- **年份**: {{ paper.year }}
- **引用数**: {{ paper.citationCount }}
- **质量评分**: {{ "%.1f"|format(paper.quality_score) if paper.quality_score else 'N/A' }}

**摘要**: {{ paper.abstract[:300] }}...

---
{% endfor %}

## 附录

### 数据来源
{% for source in data_sources %}
- {{ source }}
{% endfor %}

### 生成信息
- **系统**: AI4S-Discovery v{{ version }}
- **生成时间**: {{ timestamp }}
- **处理时长**: {{ processing_time }}秒

---

*本报告由 AI4S-Discovery 自动生成*
""",
        
        'grant_proposal': """# {{ title }}

## 项目基本信息

- **项目名称**: {{ project_name }}
- **申请人**: {{ applicant }}
- **申请单位**: {{ institution }}
- **申请日期**: {{ timestamp }}

---

## 一、立项依据

### 1.1 研究背景

{{ background }}

### 1.2 国内外研究现状

{% if literature_review %}
{{ literature_review }}
{% endif %}

### 1.3 研究意义

{{ significance }}

## 二、研究内容

### 2.1 研究目标

{{ objectives }}

### 2.2 研究内容

{% for content in research_contents %}
#### {{ loop.index }}. {{ content.title }}

{{ content.description }}
{% endfor %}

### 2.3 关键科学问题

{% for problem in key_problems %}
- {{ problem }}
{% endfor %}

## 三、研究方案

### 3.1 研究方法

{{ methodology }}

### 3.2 技术路线

{{ technical_route }}

### 3.3 可行性分析

{{ feasibility }}

## 四、创新点

{% for innovation in innovations %}
### {{ loop.index }}. {{ innovation.title }}

{{ innovation.description }}
{% endfor %}

## 五、研究基础

### 5.1 前期研究成果

{{ previous_work }}

### 5.2 研究条件

{{ research_conditions }}

## 六、预期成果

{% for outcome in expected_outcomes %}
- {{ outcome }}
{% endfor %}

## 七、研究计划

{% for phase in timeline %}
### {{ phase.name }} ({{ phase.duration }})

{{ phase.tasks }}
{% endfor %}

## 八、经费预算

| 项目 | 金额（万元） | 说明 |
|------|-------------|------|
{% for item in budget %}
| {{ item.category }} | {{ item.amount }} | {{ item.description }} |
{% endfor %}
| **合计** | **{{ total_budget }}** | |

---

*本申请书由 AI4S-Discovery 辅助生成*
""",
        
        'literature_review': """# {{ title }}

**作者**: {{ author }}  
**日期**: {{ timestamp }}

---

## 摘要

{{ abstract }}

## 1. 引言

{{ introduction }}

## 2. 研究方法

本综述通过系统检索以下数据库：
{% for source in data_sources %}
- {{ source }}
{% endfor %}

检索时间范围：{{ year_range }}  
检索关键词：{{ keywords }}  
文献筛选标准：{{ selection_criteria }}

## 3. 研究现状

### 3.1 发展历程

{{ development_history }}

### 3.2 主要研究方向

{% for direction in research_directions %}
#### 3.2.{{ loop.index }} {{ direction.name }}

{{ direction.description }}

**代表性工作**:
{% for work in direction.representative_works %}
- {{ work.authors }} ({{ work.year }}). {{ work.title }}. *{{ work.journal }}*. 引用数: {{ work.citations }}
{% endfor %}
{% endfor %}

### 3.3 研究热点

{% for topic in hot_topics %}
- **{{ topic.name }}**: {{ topic.description }} (相关文献: {{ topic.paper_count }}篇)
{% endfor %}

## 4. 研究趋势

### 4.1 发展趋势

{{ trends }}

### 4.2 技术演进

{{ technical_evolution }}

### 4.3 未来方向

{% for direction in future_directions %}
- {{ direction }}
{% endfor %}

## 5. 研究空白与挑战

### 5.1 研究空白

{% for gap in research_gaps %}
#### {{ loop.index }}. {{ gap.title }}

{{ gap.description }}
{% endfor %}

### 5.2 面临挑战

{% for challenge in challenges %}
- **{{ challenge.type }}**: {{ challenge.description }}
{% endfor %}

## 6. 结论

{{ conclusion }}

## 参考文献

{% for ref in references %}
[{{ loop.index }}] {{ ref.authors }}. {{ ref.title }}. *{{ ref.journal }}*, {{ ref.year }}, {{ ref.volume }}({{ ref.issue }}): {{ ref.pages }}.
{% endfor %}

---

*本综述由 AI4S-Discovery 辅助生成*
""",
        
        'patent_analysis': """# {{ title }}

**分析日期**: {{ timestamp }}  
**技术领域**: {{ technical_field }}

---

## 执行摘要

{{ summary }}

## 专利统计

- **专利总数**: {{ patent_count }}
- **申请人数量**: {{ applicant_count }}
- **年份范围**: {{ year_range }}
- **主要国家/地区**: {{ regions }}

## 技术分布

{% for category in tech_categories %}
### {{ category.name }}

- **专利数量**: {{ category.count }}
- **占比**: {{ "%.1f"|format(category.percentage) }}%
- **主要申请人**: {{ category.top_applicants|join(', ') }}
{% endfor %}

## 主要申请人分析

{% for applicant in top_applicants %}
### {{ loop.index }}. {{ applicant.name }}

- **专利数量**: {{ applicant.patent_count }}
- **市场份额**: {{ "%.1f"|format(applicant.market_share) }}%
- **技术重点**: {{ applicant.focus_areas|join(', ') }}
- **近期动态**: {{ applicant.recent_trends }}
{% endfor %}

## 技术演进

{{ technical_evolution }}

## 专利空白分析

{% for gap in patent_gaps %}
### {{ gap.title }}

{{ gap.description }}

**机会评估**: {{ gap.opportunity_score }}/10
{% endfor %}

## 竞争态势

{{ competitive_landscape }}

## 建议

{% for recommendation in recommendations %}
- {{ recommendation }}
{% endfor %}

---

*本报告由 AI4S-Discovery 自动生成*
"""
    }
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化报告生成器
        
        Args:
            template_dir: 自定义模板目录
        """
        self.template_dir = template_dir or str(Path(__file__).parent.parent.parent / "templates")
        
        # 创建模板目录
        Path(self.template_dir).mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=False
        )
        
        # 保存内置模板
        self._save_builtin_templates()
        
        logger.info("报告生成器初始化完成")
    
    def _save_builtin_templates(self):
        """保存内置模板到文件"""
        for name, content in self.TEMPLATES.items():
            template_path = Path(self.template_dir) / f"{name}.md"
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def generate_report(
        self,
        template_name: str,
        data: Dict[str, Any],
        output_format: str = 'markdown',
        output_path: Optional[str] = None
    ) -> str:
        """
        生成报告
        
        Args:
            template_name: 模板名称
            data: 报告数据
            output_format: 输出格式 (markdown/html/pdf)
            output_path: 输出文件路径
        
        Returns:
            生成的报告内容或文件路径
        """
        logger.info(f"生成报告: {template_name}, 格式: {output_format}")
        
        # 添加默认数据
        data.setdefault('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        data.setdefault('version', settings.VERSION)
        
        # 加载模板
        if template_name in self.TEMPLATES:
            template = Template(self.TEMPLATES[template_name])
        else:
            template_path = Path(self.template_dir) / f"{template_name}.md"
            if not template_path.exists():
                raise FileNotFoundError(f"模板不存在: {template_name}")
            template = self.env.get_template(f"{template_name}.md")
        
        # 渲染Markdown
        markdown_content = template.render(**data)
        
        # 根据输出格式处理
        if output_format == 'markdown':
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.success(f"Markdown报告已保存: {output_path}")
                return output_path
            return markdown_content
        
        elif output_format == 'html':
            html_content = self._markdown_to_html(markdown_content, data.get('title', '报告'))
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.success(f"HTML报告已保存: {output_path}")
                return output_path
            return html_content
        
        elif output_format == 'pdf':
            if not output_path:
                output_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            html_content = self._markdown_to_html(markdown_content, data.get('title', '报告'))
            self._html_to_pdf(html_content, output_path)
            logger.success(f"PDF报告已保存: {output_path}")
            return output_path
        
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
    
    def _markdown_to_html(self, markdown_content: str, title: str) -> str:
        """将Markdown转换为HTML"""
        html_body = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'codehilite']
        )
        
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin-left: 0;
            color: #7f8c8d;
        }}
        ul, ol {{
            padding-left: 30px;
        }}
        li {{
            margin: 8px 0;
        }}
        hr {{
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #95a5a6;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    {html_body}
    <div class="footer">
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
        return html_template
    
    def _html_to_pdf(self, html_content: str, output_path: str):
        """将HTML转换为PDF"""
        try:
            HTML(string=html_content).write_pdf(output_path)
        except Exception as e:
            logger.error(f"PDF生成失败: {e}")
            logger.warning("尝试使用简化方法生成PDF")
            # 如果WeasyPrint失败，保存为HTML
            html_path = output_path.replace('.pdf', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"已保存为HTML格式: {html_path}")
    
    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        templates = list(self.TEMPLATES.keys())
        
        # 添加自定义模板
        for file in Path(self.template_dir).glob("*.md"):
            name = file.stem
            if name not in templates:
                templates.append(name)
        
        return templates
    
    def add_custom_template(self, name: str, content: str):
        """
        添加自定义模板
        
        Args:
            name: 模板名称
            content: 模板内容（Jinja2格式）
        """
        template_path = Path(self.template_dir) / f"{name}.md"
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"自定义模板已添加: {name}")


# 创建全局报告生成器实例
report_generator = ReportGenerator()