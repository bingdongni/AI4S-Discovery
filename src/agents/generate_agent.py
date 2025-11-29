#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成智能体（Generate Agent）
负责创新假设生成、跨域知识迁移推荐和反事实推理
使用LLM驱动的智能生成
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from src.core.config import settings
from src.utils.llm_client import generate_text


class HypothesisGenerator:
    """创新假设生成器（LLM驱动）"""
    
    async def generate_hypotheses(
        self,
        research_gaps: List[Dict],
        papers: List[Dict],
        count: int = 5
    ) -> List[Dict]:
        """
        生成创新假设
        
        基于研究空白和现有文献，使用LLM生成可验证的创新假设
        
        Args:
            research_gaps: 研究空白列表
            papers: 文献列表
            count: 生成数量
        
        Returns:
            List[Dict]: 创新假设列表
        """
        logger.info(f"开始生成 {count} 个创新假设")
        
        hypotheses = []
        
        # 准备上下文信息
        context = self._prepare_context(research_gaps, papers)
        
        for i, gap in enumerate(research_gaps[:count]):
            try:
                # 构建提示词
                prompt = self._build_hypothesis_prompt(gap, context, i+1)
                
                # 使用LLM生成假设
                response = await generate_text(
                    prompt,
                    max_tokens=settings.HYPOTHESIS_MAX_TOKENS,
                    temperature=settings.HYPOTHESIS_TEMPERATURE
                )
                
                # 解析LLM响应
                hypothesis = self._parse_hypothesis_response(response, gap, i+1)
                
                # 添加支撑文献
                hypothesis['supporting_papers'] = self._find_supporting_papers(gap, papers)
                
                hypotheses.append(hypothesis)
                logger.debug(f"生成假设 {i+1}: {hypothesis['title']}")
                
            except Exception as e:
                logger.error(f"生成假设 {i+1} 失败: {e}")
                # 使用备用方法
                hypothesis = self._generate_fallback_hypothesis(gap, papers, i+1)
                hypotheses.append(hypothesis)
        
        logger.success(f"成功生成 {len(hypotheses)} 个创新假设")
        return hypotheses
    
    def _prepare_context(self, research_gaps: List[Dict], papers: List[Dict]) -> str:
        """准备上下文信息"""
        # 提取高质量文献
        top_papers = sorted(
            papers,
            key=lambda x: x.get('quality_score', 0),
            reverse=True
        )[:10]
        
        context = "## 研究背景\n\n"
        context += f"分析了 {len(papers)} 篇相关文献，发现 {len(research_gaps)} 个研究空白。\n\n"
        
        context += "## 高质量文献\n\n"
        for i, paper in enumerate(top_papers[:5], 1):
            context += f"{i}. {paper.get('title', '未知标题')}\n"
            context += f"   - 质量评分: {paper.get('quality_score', 0)}\n"
            if paper.get('abstract'):
                context += f"   - 摘要: {paper['abstract'][:200]}...\n"
        
        return context
    
    def _build_hypothesis_prompt(self, gap: Dict, context: str, index: int) -> str:
        """构建假设生成提示词"""
        gap_type = gap.get('type', 'unknown')
        priority = gap.get('priority', 'medium')
        
        prompt = f"""你是一位资深科研专家，擅长发现研究机会并提出创新假设。

{context}

## 研究空白 #{index}

类型: {gap_type}
优先级: {priority}
"""
        
        if gap_type == 'under_researched_concept':
            concept = gap.get('concept', '未知概念')
            prompt += f"概念: {concept}\n"
            prompt += f"当前研究数量: {gap.get('paper_count', 0)}\n\n"
            prompt += f"请针对「{concept}」这个研究不足的概念，提出一个创新的研究假设。"
        
        elif gap_type == 'missing_cross_domain':
            concepts = gap.get('concepts', [])
            if len(concepts) >= 2:
                prompt += f"领域1: {concepts[0]}\n"
                prompt += f"领域2: {concepts[1]}\n\n"
                prompt += f"请提出一个结合「{concepts[0]}」和「{concepts[1]}」的跨域创新假设。"
        
        else:
            prompt += "\n请基于上述研究空白，提出一个创新的研究假设。"
        
        prompt += """

请按以下JSON格式输出（不要包含markdown代码块标记）：
{
    "title": "假设标题（简洁明了）",
    "description": "详细描述（200-300字）",
    "rationale": "理论依据（说明为什么这个假设有价值）",
    "feasibility": {
        "technical": "high/medium/low",
        "resource": "high/medium/low",
        "time": "short/medium/long"
    },
    "expected_impact": "high/medium/low",
    "required_resources": {
        "funding": "预估资金（如$100K-200K）",
        "team_size": "团队规模（如3-5人）",
        "equipment": ["设备1", "设备2"],
        "duration": "预计时间（如12-18个月）"
    },
    "timeline": "研究周期",
    "confidence": 0.75
}
"""
        
        return prompt
    
    def _parse_hypothesis_response(self, response: str, gap: Dict, index: int) -> Dict:
        """解析LLM响应"""
        try:
            # 清理响应（移除可能的markdown标记）
            response = response.strip()
            if response.startswith('```'):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1]) if len(lines) > 2 else response
            
            # 尝试解析JSON
            hypothesis = json.loads(response)
            
            # 添加ID
            hypothesis['id'] = f"H{index}"
            
            # 验证必需字段
            required_fields = ['title', 'description', 'rationale']
            for field in required_fields:
                if field not in hypothesis:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 设置默认值
            hypothesis.setdefault('feasibility', {
                'technical': 'medium',
                'resource': 'medium',
                'time': 'medium'
            })
            hypothesis.setdefault('expected_impact', 'medium')
            hypothesis.setdefault('confidence', 0.75)
            hypothesis.setdefault('timeline', '12-18个月')
            
            return hypothesis
            
        except Exception as e:
            logger.warning(f"解析LLM响应失败: {e}，使用备用方法")
            return self._generate_fallback_hypothesis(gap, [], index)
    
    def _generate_fallback_hypothesis(self, gap: Dict, papers: List[Dict], index: int) -> Dict:
        """备用假设生成方法"""
        gap_type = gap.get('type', 'unknown')
        priority = gap.get('priority', 'medium')
        
        if gap_type == 'under_researched_concept':
            concept = gap.get('concept', '未知领域')
            title = f"探索{concept}的创新应用"
            description = f"将{concept}应用于新的研究场景，填补当前研究空白。通过跨域方法迁移，探索{concept}在不同领域的创新应用潜力。"
        elif gap_type == 'missing_cross_domain':
            concepts = gap.get('concepts', ['领域A', '领域B'])
            title = f"结合{concepts[0]}和{concepts[1]}的跨域研究"
            description = f"融合{concepts[0]}和{concepts[1]}的优势，探索跨域创新机会。通过整合两个领域的方法论，可能产生突破性成果。"
        else:
            title = "探索新的研究方向"
            description = "基于现有研究空白，提出创新的研究假设，填补学术界的知识缺口。"
        
        return {
            'id': f"H{index}",
            'title': title,
            'description': description,
            'rationale': f"基于对相关文献的分析，该方向具有{priority}优先级，存在明显的研究机会。",
            'feasibility': {
                'technical': 'medium',
                'resource': 'medium',
                'time': 'medium'
            },
            'expected_impact': priority,
            'required_resources': {
                'funding': '$100K-200K',
                'team_size': '3-5人',
                'equipment': ['标准实验设备', '计算资源'],
                'duration': '12-18个月'
            },
            'timeline': '12-18个月',
            'confidence': 0.70,
        }
    
    def _find_supporting_papers(self, gap: Dict, papers: List[Dict]) -> List[str]:
        """查找支撑文献"""
        sorted_papers = sorted(
            papers,
            key=lambda x: x.get('quality_score', 0),
            reverse=True
        )
        
        return [p.get('title', '')[:100] for p in sorted_papers[:3]]


class CounterfactualReasoner:
    """反事实推理器（LLM驱动）"""
    
    async def reason_counterfactuals(
        self,
        hypothesis: Dict,
        papers: List[Dict],
        trl_result: Optional[Dict] = None
    ) -> List[Dict]:
        """
        进行反事实推理
        
        分析"如果采用不同的方法/条件，会产生什么结果"
        
        Args:
            hypothesis: 研究假设
            papers: 相关文献
            trl_result: TRL评估结果
        
        Returns:
            List[Dict]: 反事实场景列表
        """
        logger.info(f"开始反事实推理: {hypothesis.get('title', 'Unknown')}")
        
        try:
            # 构建提示词
            prompt = self._build_counterfactual_prompt(hypothesis, papers, trl_result)
            
            # 使用LLM生成反事实场景
            response = await generate_text(
                prompt,
                max_tokens=1024,
                temperature=0.7
            )
            
            # 解析响应
            scenarios = self._parse_counterfactual_response(response)
            
            logger.success(f"生成 {len(scenarios)} 个反事实场景")
            return scenarios
            
        except Exception as e:
            logger.error(f"反事实推理失败: {e}")
            return self._generate_fallback_scenarios(hypothesis)
    
    def _build_counterfactual_prompt(
        self,
        hypothesis: Dict,
        papers: List[Dict],
        trl_result: Optional[Dict]
    ) -> str:
        """构建反事实推理提示词"""
        prompt = f"""你是一位科研战略分析专家，擅长反事实推理和风险评估。

## 研究假设

标题: {hypothesis.get('title', 'Unknown')}
描述: {hypothesis.get('description', 'No description')}
当前可行性: {hypothesis.get('feasibility', {})}
"""
        
        if trl_result:
            prompt += f"\n当前TRL等级: {trl_result.get('trl_level', 'Unknown')}\n"
        
        prompt += f"""
## 任务

请进行反事实推理，分析以下{settings.COUNTERFACTUAL_SCENARIOS}个场景：
1. 如果采用不同的技术路线
2. 如果改变资源投入水平
3. 如果调整研究时间线

对每个场景，分析：
- 可能的结果
- 成功概率
- 潜在风险
- 所需调整

请按以下JSON格式输出（不要包含markdown代码块标记）：
[
    {{
        "scenario": "场景描述",
        "condition_change": "改变的条件",
        "expected_outcome": "预期结果",
        "success_probability": 0.75,
        "risks": ["风险1", "风险2"],
        "required_adjustments": ["调整1", "调整2"],
        "impact_on_timeline": "对时间线的影响",
        "impact_on_resources": "对资源的影响"
    }}
]
"""
        
        return prompt
    
    def _parse_counterfactual_response(self, response: str) -> List[Dict]:
        """解析反事实推理响应"""
        try:
            # 清理响应
            response = response.strip()
            if response.startswith('```'):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1]) if len(lines) > 2 else response
            
            scenarios = json.loads(response)
            
            # 验证和补充
            for i, scenario in enumerate(scenarios):
                scenario.setdefault('id', f"CF{i+1}")
                scenario.setdefault('success_probability', 0.5)
                scenario.setdefault('risks', [])
                scenario.setdefault('required_adjustments', [])
            
            return scenarios
            
        except Exception as e:
            logger.warning(f"解析反事实响应失败: {e}")
            return []
    
    def _generate_fallback_scenarios(self, hypothesis: Dict) -> List[Dict]:
        """备用反事实场景生成"""
        return [
            {
                'id': 'CF1',
                'scenario': '采用不同的技术路线',
                'condition_change': '使用更成熟的技术方案',
                'expected_outcome': '降低技术风险，但可能减少创新性',
                'success_probability': 0.75,
                'risks': ['创新性降低', '竞争优势减弱'],
                'required_adjustments': ['重新评估技术方案', '调整研究目标'],
                'impact_on_timeline': '可能缩短6个月',
                'impact_on_resources': '降低20%技术风险成本'
            },
            {
                'id': 'CF2',
                'scenario': '增加资源投入',
                'condition_change': '扩大团队规模和资金投入',
                'expected_outcome': '加快研发进度，提高成功率',
                'success_probability': 0.80,
                'risks': ['成本增加', '管理复杂度提升'],
                'required_adjustments': ['优化团队结构', '加强项目管理'],
                'impact_on_timeline': '可能缩短30%时间',
                'impact_on_resources': '增加40-50%预算'
            },
            {
                'id': 'CF3',
                'scenario': '调整研究范围',
                'condition_change': '聚焦核心问题，缩小研究范围',
                'expected_outcome': '更快产出成果，但覆盖面减少',
                'success_probability': 0.85,
                'risks': ['研究深度可能不足', '后续扩展困难'],
                'required_adjustments': ['明确核心目标', '制定分阶段计划'],
                'impact_on_timeline': '缩短40%',
                'impact_on_resources': '降低30%资源需求'
            }
        ]


class CrossDomainTransferRecommender:
    """跨域知识迁移推荐器（LLM驱动）"""
    
    async def recommend_transfers(
        self,
        source_domain: str,
        target_domain: str,
        papers: List[Dict]
    ) -> List[Dict]:
        """
        推荐跨域知识迁移方案
        
        Args:
            source_domain: 源领域
            target_domain: 目标领域
            papers: 文献列表
        
        Returns:
            List[Dict]: 迁移推荐列表
        """
        logger.info(f"生成跨域迁移推荐: {source_domain} -> {target_domain}")
        
        try:
            # 构建提示词
            prompt = self._build_transfer_prompt(source_domain, target_domain, papers)
            
            # 使用LLM生成推荐
            response = await generate_text(
                prompt,
                max_tokens=1024,
                temperature=0.7
            )
            
            # 解析响应
            recommendations = self._parse_transfer_response(response, source_domain, target_domain)
            
            logger.success(f"生成 {len(recommendations)} 个迁移推荐")
            return recommendations
            
        except Exception as e:
            logger.error(f"跨域迁移推荐失败: {e}")
            return self._generate_fallback_transfers(source_domain, target_domain)
    
    def _build_transfer_prompt(
        self,
        source_domain: str,
        target_domain: str,
        papers: List[Dict]
    ) -> str:
        """构建迁移推荐提示词"""
        # 提取源领域的关键方法
        top_papers = sorted(papers, key=lambda x: x.get('quality_score', 0), reverse=True)[:5]
        
        prompt = f"""你是一位跨学科研究专家，擅长发现不同领域之间的知识迁移机会。

## 任务

源领域: {source_domain}
目标领域: {target_domain}

## 源领域高质量文献

"""
        
        for i, paper in enumerate(top_papers, 1):
            prompt += f"{i}. {paper.get('title', 'Unknown')}\n"
        
        prompt += f"""

请分析从「{source_domain}」到「{target_domain}」的知识迁移机会，提出3个具体的迁移方案。

请按以下JSON格式输出（不要包含markdown代码块标记）：
[
    {{
        "source_method": "源领域的方法/技术",
        "target_application": "在目标领域的应用",
        "similarity_score": 0.85,
        "expected_benefit": "预期收益",
        "challenges": ["挑战1", "挑战2"],
        "success_probability": 0.75,
        "implementation_steps": ["步骤1", "步骤2", "步骤3"]
    }}
]
"""
        
        return prompt
    
    def _parse_transfer_response(
        self,
        response: str,
        source_domain: str,
        target_domain: str
    ) -> List[Dict]:
        """解析迁移推荐响应"""
        try:
            response = response.strip()
            if response.startswith('```'):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1]) if len(lines) > 2 else response
            
            recommendations = json.loads(response)
            
            for i, rec in enumerate(recommendations):
                rec['id'] = f"T{i+1}"
                rec['source_domain'] = source_domain
                rec['target_domain'] = target_domain
                rec.setdefault('similarity_score', 0.7)
                rec.setdefault('success_probability', 0.6)
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"解析迁移推荐响应失败: {e}")
            return []
    
    def _generate_fallback_transfers(self, source_domain: str, target_domain: str) -> List[Dict]:
        """备用迁移推荐"""
        return [
            {
                'id': 'T1',
                'source_domain': source_domain,
                'target_domain': target_domain,
                'source_method': f'{source_domain}的核心方法',
                'target_application': f'应用于{target_domain}的数据分析',
                'similarity_score': 0.75,
                'expected_benefit': '提升效率30-40%',
                'challenges': ['数据格式差异', '领域知识迁移'],
                'success_probability': 0.70,
                'implementation_steps': [
                    '1. 分析方法适用性',
                    '2. 调整参数和模型',
                    '3. 小规模验证',
                    '4. 全面推广应用'
                ]
            }
        ]


class GenerateAgent:
    """
    生成智能体（LLM驱动）
    
    核心职责：
    1. 创新假设生成
    2. 反事实推理
    3. 跨域知识迁移推荐
    """
    
    def __init__(self):
        """初始化生成智能体"""
        self.hypothesis_generator = HypothesisGenerator()
        self.counterfactual_reasoner = CounterfactualReasoner()
        self.transfer_recommender = CrossDomainTransferRecommender()
        
        logger.info("生成智能体初始化完成（LLM驱动）")
    
    async def generate_innovations(
        self,
        research_gaps: List[Dict],
        papers: List[Dict],
        domains: List[str] = None,
        trl_results: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        生成创新建议
        
        Args:
            research_gaps: 研究空白列表
            papers: 文献列表
            domains: 研究领域列表
            trl_results: TRL评估结果
        
        Returns:
            Dict: 创新建议结果
        """
        logger.info("开始生成创新建议（LLM驱动）")
        
        # 生成假设
        hypotheses = await self.hypothesis_generator.generate_hypotheses(
            research_gaps, papers, count=settings.HYPOTHESIS_COUNT
        )
        
        # 反事实推理
        counterfactuals = []
        for i, hypothesis in enumerate(hypotheses[:3]):  # 对前3个假设进行反事实推理
            trl_result = trl_results[i] if trl_results and i < len(trl_results) else None
            scenarios = await self.counterfactual_reasoner.reason_counterfactuals(
                hypothesis, papers, trl_result
            )
            counterfactuals.append({
                'hypothesis_id': hypothesis['id'],
                'scenarios': scenarios
            })
        
        # 跨域迁移推荐
        transfers = []
        if domains and len(domains) >= 2:
            for i in range(min(len(domains) - 1, 2)):  # 最多2对领域
                transfer = await self.transfer_recommender.recommend_transfers(
                    domains[i], domains[i+1], papers
                )
                transfers.extend(transfer)
        
        result = {
            'hypotheses': hypotheses,
            'counterfactual_reasoning': counterfactuals,
            'cross_domain_transfers': transfers,
            'total_suggestions': len(hypotheses) + len(transfers),
            'high_confidence_count': sum(
                1 for h in hypotheses if h.get('confidence', 0) > 0.8
            ),
            'timestamp': datetime.now().isoformat(),
            'llm_driven': True,
        }
        
        logger.success(
            f"创新建议生成完成: {result['total_suggestions']} 个建议, "
            f"{len(counterfactuals)} 个反事实分析"
        )
        
        return result


# 创建全局生成智能体实例
generate_agent = GenerateAgent()
