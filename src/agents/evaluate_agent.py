#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
评估智能体（Evaluate Agent）
负责TRL（技术成熟度）评估和假设可行性验证
"""

import random
from typing import Dict, List, Any
from datetime import datetime
from loguru import logger
import numpy as np

from src.core.config import settings


class TRLAssessor:
    """TRL评估器"""
    
    TRL_LEVELS = {
        1: "基础原理观察和报告",
        2: "技术概念形成",
        3: "概念验证",
        4: "实验室验证",
        5: "相关环境验证",
        6: "相关环境演示",
        7: "系统原型演示",
        8: "系统完成和验证",
        9: "实际系统验证",
    }
    
    def assess_trl(self, papers: List[Dict], concept: str) -> Dict:
        """
        评估技术成熟度
        
        Args:
            papers: 文献列表
            concept: 研究概念
        
        Returns:
            Dict: TRL评估结果
        """
        logger.info(f"开始TRL评估: {concept}")
        
        # 基于文献数量和时间跨度评估
        paper_count = len(papers)
        years = [p.get('year', 0) for p in papers if p.get('year', 0) > 0]
        year_span = max(years) - min(years) if len(years) > 1 else 0
        
        # 计算平均引用数
        citations = [p.get('citationCount', 0) for p in papers]
        avg_citations = np.mean(citations) if citations else 0
        
        # 简化的TRL评估逻辑
        trl_level = self._calculate_trl_level(
            paper_count, year_span, avg_citations, papers
        )
        
        # 检查应用案例
        has_applications = self._check_applications(papers)
        has_prototypes = self._check_prototypes(papers)
        has_commercial = self._check_commercial(papers)
        
        # 根据应用情况调整TRL
        if has_commercial and trl_level < 9:
            trl_level = min(trl_level + 2, 9)
        elif has_prototypes and trl_level < 7:
            trl_level = min(trl_level + 1, 7)
        elif has_applications and trl_level < 6:
            trl_level = min(trl_level + 1, 6)
        
        confidence = self._calculate_confidence(paper_count, year_span)
        
        return {
            'level': trl_level,
            'description': self.TRL_LEVELS[trl_level],
            'confidence': confidence,
            'evidence': {
                'paper_count': paper_count,
                'year_span': year_span,
                'avg_citations': round(avg_citations, 2),
                'has_applications': has_applications,
                'has_prototypes': has_prototypes,
                'has_commercial': has_commercial,
            },
            'next_steps': self._suggest_next_steps(trl_level),
            'estimated_time_to_market': self._estimate_time_to_market(trl_level),
        }
    
    def _calculate_trl_level(
        self,
        paper_count: int,
        year_span: int,
        avg_citations: float,
        papers: List[Dict]
    ) -> int:
        """计算TRL等级"""
        
        # 基础评分
        if paper_count < 10:
            base_level = random.randint(1, 3)
        elif paper_count < 50:
            base_level = random.randint(3, 5)
        elif paper_count < 200:
            base_level = random.randint(5, 7)
        else:
            base_level = random.randint(7, 9)
        
        # 根据时间跨度调整
        if year_span > 10:
            base_level = min(base_level + 1, 9)
        
        # 根据引用数调整
        if avg_citations > 100:
            base_level = min(base_level + 1, 9)
        
        return base_level
    
    def _check_applications(self, papers: List[Dict]) -> bool:
        """检查是否有应用案例"""
        keywords = ['application', 'applied', 'implementation', 'deployment']
        
        for paper in papers[:20]:
            abstract = paper.get('abstract', '').lower()
            if any(kw in abstract for kw in keywords):
                return True
        return False
    
    def _check_prototypes(self, papers: List[Dict]) -> bool:
        """检查是否有原型系统"""
        keywords = ['prototype', 'system', 'platform', 'framework']
        
        for paper in papers[:20]:
            abstract = paper.get('abstract', '').lower()
            title = paper.get('title', '').lower()
            if any(kw in abstract or kw in title for kw in keywords):
                return True
        return False
    
    def _check_commercial(self, papers: List[Dict]) -> bool:
        """检查是否有商业化应用"""
        keywords = ['commercial', 'product', 'industry', 'market']
        
        for paper in papers[:20]:
            abstract = paper.get('abstract', '').lower()
            if any(kw in abstract for kw in keywords):
                return True
        return False
    
    def _calculate_confidence(self, paper_count: int, year_span: int) -> float:
        """计算置信度"""
        # 基于文献数量和时间跨度计算置信度
        count_score = min(paper_count / 100, 1.0)
        span_score = min(year_span / 15, 1.0)
        
        confidence = (count_score * 0.6 + span_score * 0.4) * 0.3 + 0.7
        return round(min(confidence, 0.95), 2)
    
    def _suggest_next_steps(self, current_level: int) -> List[str]:
        """建议下一步行动"""
        suggestions = {
            1: ["进行更多基础研究", "建立理论模型", "发表基础研究论文"],
            2: ["设计概念验证实验", "寻找合作伙伴", "申请初步研究资金"],
            3: ["进行实验室验证", "优化实验方案", "收集初步数据"],
            4: ["扩大实验规模", "优化技术参数", "进行重复性验证"],
            5: ["在相关环境中测试", "收集用户反馈", "评估实际性能"],
            6: ["开发原型系统", "进行市场调研", "寻找潜在客户"],
            7: ["完善系统功能", "准备商业化", "申请专利保护"],
            8: ["进行大规模验证", "建立生产线", "制定质量标准"],
            9: ["持续优化改进", "扩大市场份额", "开发衍生产品"],
        }
        return suggestions.get(current_level, ["继续研究和开发"])
    
    def _estimate_time_to_market(self, trl_level: int) -> str:
        """估算上市时间"""
        time_estimates = {
            1: "10-15年",
            2: "8-12年",
            3: "6-10年",
            4: "5-8年",
            5: "4-6年",
            6: "3-5年",
            7: "2-4年",
            8: "1-3年",
            9: "已上市或即将上市",
        }
        return time_estimates.get(trl_level, "未知")


class FeasibilityValidator:
    """可行性验证器"""
    
    def validate_hypothesis(self, hypothesis: Dict, papers: List[Dict]) -> Dict:
        """
        验证假设可行性
        
        Args:
            hypothesis: 假设信息
            papers: 文献列表
        
        Returns:
            Dict: 验证结果
        """
        logger.info(f"验证假设可行性: {hypothesis.get('id')}")
        
        # 技术可行性评估
        technical_score = self._assess_technical_feasibility(hypothesis, papers)
        
        # 资源可行性评估
        resource_score = self._assess_resource_feasibility(hypothesis)
        
        # 时间可行性评估
        time_score = self._assess_time_feasibility(hypothesis)
        
        # 市场可行性评估
        market_score = self._assess_market_feasibility(hypothesis, papers)
        
        # 综合评分
        overall_score = (
            technical_score * 0.35 +
            resource_score * 0.25 +
            time_score * 0.20 +
            market_score * 0.20
        )
        
        is_feasible = overall_score >= settings.HYPOTHESIS_MIN_CONFIDENCE
        
        return {
            'hypothesis_id': hypothesis.get('id'),
            'hypothesis_title': hypothesis.get('title'),
            'is_feasible': is_feasible,
            'scores': {
                'technical': round(technical_score, 2),
                'resource': round(resource_score, 2),
                'time': round(time_score, 2),
                'market': round(market_score, 2),
                'overall': round(overall_score, 2),
            },
            'risks': self._identify_risks(hypothesis, overall_score),
            'recommendations': self._generate_recommendations(overall_score, is_feasible),
            'priority': self._determine_priority(overall_score),
        }
    
    def _assess_technical_feasibility(self, hypothesis: Dict, papers: List[Dict]) -> float:
        """评估技术可行性"""
        # 基于假设的置信度和支撑文献数量
        confidence = hypothesis.get('confidence', 0.5)
        supporting_papers = len(hypothesis.get('supporting_papers', []))
        
        paper_score = min(supporting_papers / 5, 1.0)
        
        return confidence * 0.6 + paper_score * 0.4
    
    def _assess_resource_feasibility(self, hypothesis: Dict) -> float:
        """评估资源可行性"""
        resources = hypothesis.get('required_resources', {})
        
        # 解析资金需求
        funding_str = resources.get('funding', '$100K')
        funding_amount = int(''.join(filter(str.isdigit, funding_str)))
        
        # 资金越少，可行性越高
        if funding_amount < 100:
            funding_score = 0.9
        elif funding_amount < 300:
            funding_score = 0.7
        else:
            funding_score = 0.5
        
        # 团队规模
        team_str = resources.get('team_size', '3人')
        team_size = int(''.join(filter(str.isdigit, team_str)))
        
        if team_size <= 3:
            team_score = 0.9
        elif team_size <= 6:
            team_score = 0.7
        else:
            team_score = 0.5
        
        return (funding_score + team_score) / 2
    
    def _assess_time_feasibility(self, hypothesis: Dict) -> float:
        """评估时间可行性"""
        timeline = hypothesis.get('timeline', '12个月')
        months = int(''.join(filter(str.isdigit, timeline)))
        
        # 时间越短，可行性相对越高（但也要考虑合理性）
        if months <= 12:
            return 0.9
        elif months <= 18:
            return 0.8
        elif months <= 24:
            return 0.7
        else:
            return 0.6
    
    def _assess_market_feasibility(self, hypothesis: Dict, papers: List[Dict]) -> float:
        """评估市场可行性"""
        expected_impact = hypothesis.get('expected_impact', 'medium')
        
        impact_scores = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5,
        }
        
        return impact_scores.get(expected_impact, 0.6)
    
    def _identify_risks(self, hypothesis: Dict, overall_score: float) -> List[Dict]:
        """识别风险"""
        risks = []
        
        if overall_score < 0.6:
            risks.append({
                'type': 'high_risk',
                'description': '整体可行性较低，需要重新评估',
                'severity': 'high',
            })
        
        resources = hypothesis.get('required_resources', {})
        funding_str = resources.get('funding', '$100K')
        funding_amount = int(''.join(filter(str.isdigit, funding_str)))
        
        if funding_amount > 300:
            risks.append({
                'type': 'funding_risk',
                'description': '资金需求较大，可能难以获得充足支持',
                'severity': 'medium',
            })
        
        timeline = hypothesis.get('timeline', '12个月')
        months = int(''.join(filter(str.isdigit, timeline)))
        
        if months > 24:
            risks.append({
                'type': 'time_risk',
                'description': '研发周期较长，存在不确定性',
                'severity': 'medium',
            })
        
        if hypothesis.get('confidence', 1.0) < 0.7:
            risks.append({
                'type': 'technical_risk',
                'description': '技术实现存在较大不确定性',
                'severity': 'high',
            })
        
        return risks
    
    def _generate_recommendations(self, score: float, is_feasible: bool) -> List[str]:
        """生成建议"""
        if score > 0.8:
            return [
                "建议优先实施该假设",
                "可申请重点项目资助",
                "组建专门团队推进",
                "制定详细的实施计划",
            ]
        elif score > 0.7:
            return [
                "建议实施，但需要详细规划",
                "先进行小规模验证",
                "寻找合作伙伴分担风险",
                "制定风险应对预案",
            ]
        elif score > 0.6:
            return [
                "需要进一步论证可行性",
                "建议降低风险后再实施",
                "可以作为长期研究方向",
                "寻求更多专家意见",
            ]
        else:
            return [
                "当前不建议实施",
                "需要重新评估研究方向",
                "可以考虑调整研究目标",
                "建议寻找替代方案",
            ]
    
    def _determine_priority(self, score: float) -> str:
        """确定优先级"""
        if score > 0.8:
            return "高"
        elif score > 0.7:
            return "中高"
        elif score > 0.6:
            return "中"
        else:
            return "低"


class EvaluateAgent:
    """
    评估智能体
    
    核心职责：
    1. TRL技术成熟度评估
    2. 假设可行性验证
    3. 风险识别和建议
    """
    
    def __init__(self):
        """初始化评估智能体"""
        self.trl_assessor = TRLAssessor()
        self.feasibility_validator = FeasibilityValidator()
        
        logger.info("评估智能体初始化完成")
    
    async def evaluate_research(
        self,
        papers: List[Dict],
        hypotheses: List[Dict],
        concept: str = "研究主题"
    ) -> Dict[str, Any]:
        """
        评估研究
        
        Args:
            papers: 文献列表
            hypotheses: 假设列表
            concept: 研究概念
        
        Returns:
            Dict: 评估结果
        """
        logger.info(f"开始评估研究: {concept}")
        
        # TRL评估
        trl_assessment = self.trl_assessor.assess_trl(papers, concept)
        
        # 假设可行性验证
        hypothesis_validations = []
        for hypothesis in hypotheses:
            validation = self.feasibility_validator.validate_hypothesis(
                hypothesis, papers
            )
            hypothesis_validations.append(validation)
        
        # 统计信息
        feasible_count = sum(1 for v in hypothesis_validations if v['is_feasible'])
        high_priority_count = sum(
            1 for v in hypothesis_validations if v['priority'] in ['高', '中高']
        )
        
        result = {
            'trl_assessment': trl_assessment,
            'hypothesis_validations': hypothesis_validations,
            'overall_maturity': trl_assessment['level'],
            'maturity_description': trl_assessment['description'],
            'feasible_hypotheses_count': feasible_count,
            'high_priority_count': high_priority_count,
            'total_hypotheses': len(hypotheses),
            'recommendation_summary': self._generate_summary(
                trl_assessment, hypothesis_validations
            ),
            'timestamp': datetime.now().isoformat(),
        }
        
        logger.success(f"研究评估完成: TRL={trl_assessment['level']}, 可行假设={feasible_count}/{len(hypotheses)}")
        
        return result
    
    def _generate_summary(
        self,
        trl_assessment: Dict,
        validations: List[Dict]
    ) -> str:
        """生成评估总结"""
        trl_level = trl_assessment['level']
        feasible_count = sum(1 for v in validations if v['is_feasible'])
        total_count = len(validations)
        
        summary = f"该研究方向当前处于TRL {trl_level}级（{trl_assessment['description']}），"
        
        if trl_level >= 7:
            summary += "技术已相对成熟，可以考虑商业化应用。"
        elif trl_level >= 4:
            summary += "技术处于验证阶段，需要进一步完善。"
        else:
            summary += "技术处于早期阶段，需要更多基础研究。"
        
        if total_count > 0:
            feasibility_rate = feasible_count / total_count * 100
            summary += f" 在{total_count}个创新假设中，有{feasible_count}个（{feasibility_rate:.1f}%）具有较高可行性。"
        
        return summary


# 创建全局评估智能体实例
evaluate_agent = EvaluateAgent()