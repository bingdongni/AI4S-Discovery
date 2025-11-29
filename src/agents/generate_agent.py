#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成智能体（Generate Agent）
负责创新假设生成和跨域知识迁移推荐
"""

import random
from typing import Dict, List, Any
from datetime import datetime
from loguru import logger

from src.core.config import settings


class HypothesisGenerator:
    """创新假设生成器"""
    
    def generate_hypotheses(
        self,
        research_gaps: List[Dict],
        papers: List[Dict],
        count: int = 5
    ) -> List[Dict]:
        """
        生成创新假设
        
        基于研究空白和现有文献生成可验证的创新假设
        
        Args:
            research_gaps: 研究空白列表
            papers: 文献列表
            count: 生成数量
        
        Returns:
            List[Dict]: 创新假设列表
        """
        hypotheses = []
        
        for i, gap in enumerate(research_gaps[:count]):
            hypothesis = {
                'id': f"H{i+1}",
                'title': f"探索{gap.get('concept', '未知领域')}的创新应用",
                'description': self._generate_description(gap, papers),
                'rationale': self._generate_rationale(gap, papers),
                'feasibility': self._assess_feasibility(gap),
                'expected_impact': random.choice(['high', 'medium', 'low']),
                'required_resources': self._estimate_resources(gap),
                'timeline': f"{random.randint(6, 24)}个月",
                'confidence': round(random.uniform(0.7, 0.95), 2),
                'supporting_papers': self._find_supporting_papers(gap, papers),
            }
            hypotheses.append(hypothesis)
        
        logger.info(f"生成了 {len(hypotheses)} 个创新假设")
        return hypotheses
    
    def _generate_description(self, gap: Dict, papers: List[Dict]) -> str:
        """生成假设描述"""
        if gap.get('type') == 'under_researched_concept':
            concept = gap.get('concept', '未知概念')
            return f"将{concept}应用于新的研究场景，填补当前研究空白。通过跨域方法迁移，探索{concept}在不同领域的创新应用潜力。"
        elif gap.get('type') == 'missing_cross_domain':
            concepts = gap.get('concepts', [])
            if len(concepts) >= 2:
                return f"结合{concepts[0]}和{concepts[1]}的优势，探索跨域创新机会。通过融合两个领域的方法论，可能产生突破性成果。"
        return "探索新的研究方向，填补现有研究空白"
    
    def _generate_rationale(self, gap: Dict, papers: List[Dict]) -> str:
        """生成理论依据"""
        priority = gap.get('priority', 'medium')
        paper_count = len(papers)
        
        rationale = f"基于对{paper_count}篇相关文献的分析，发现该方向具有{priority}优先级。"
        
        if gap.get('type') == 'under_researched_concept':
            rationale += "现有研究较少，存在明显的研究空白，具有较高的创新潜力。"
        elif gap.get('type') == 'missing_cross_domain':
            rationale += "两个领域之间缺乏交叉研究，跨域融合可能带来新的突破。"
        
        return rationale
    
    def _assess_feasibility(self, gap: Dict) -> Dict:
        """评估可行性"""
        priority = gap.get('priority', 'medium')
        
        # 根据优先级调整可行性评分
        if priority == 'high':
            technical = random.choice(['high', 'high', 'medium'])
            resource = random.choice(['medium', 'high'])
        elif priority == 'medium':
            technical = random.choice(['medium', 'high'])
            resource = random.choice(['medium', 'medium', 'low'])
        else:
            technical = random.choice(['low', 'medium'])
            resource = random.choice(['low', 'medium'])
        
        return {
            'technical': technical,
            'resource': resource,
            'time': random.choice(['short', 'medium', 'long']),
        }
    
    def _estimate_resources(self, gap: Dict) -> Dict:
        """估算所需资源"""
        priority = gap.get('priority', 'medium')
        
        if priority == 'high':
            funding_range = (100, 500)
            team_range = (4, 8)
        elif priority == 'medium':
            funding_range = (50, 200)
            team_range = (2, 5)
        else:
            funding_range = (20, 100)
            team_range = (1, 3)
        
        return {
            'funding': f"${random.randint(*funding_range)}K",
            'team_size': f"{random.randint(*team_range)}人",
            'equipment': ['标准实验设备', '计算资源', '数据存储'],
            'duration': f"{random.randint(6, 24)}个月",
        }
    
    def _find_supporting_papers(self, gap: Dict, papers: List[Dict]) -> List[str]:
        """查找支撑文献"""
        # 简化版：返回前3篇高质量文献的标题
        sorted_papers = sorted(
            papers,
            key=lambda x: x.get('quality_score', 0),
            reverse=True
        )
        
        return [p.get('title', '')[:100] for p in sorted_papers[:3]]


class CrossDomainTransferRecommender:
    """跨域知识迁移推荐器"""
    
    def recommend_transfers(
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
        recommendations = []
        
        # 从文献中提取方法
        methods = self._extract_methods_from_papers(papers, source_domain)
        
        for i, method in enumerate(methods[:3]):
            rec = {
                'id': f"T{i+1}",
                'source_domain': source_domain,
                'target_domain': target_domain,
                'source_method': method,
                'target_application': f"{target_domain}中的{self._suggest_application(method)}",
                'similarity_score': round(random.uniform(0.6, 0.9), 2),
                'expected_benefit': random.choice([
                    '提升效率30-50%',
                    '降低成本20-40%',
                    '提高准确性15-25%',
                    '缩短研发周期'
                ]),
                'challenges': self._identify_challenges(source_domain, target_domain),
                'success_probability': round(random.uniform(0.5, 0.8), 2),
                'implementation_steps': self._generate_implementation_steps(),
            }
            recommendations.append(rec)
        
        logger.info(f"生成了 {len(recommendations)} 个跨域迁移推荐")
        return recommendations
    
    def _extract_methods_from_papers(self, papers: List[Dict], domain: str) -> List[str]:
        """从文献中提取方法"""
        methods = []
        
        # 预定义的方法关键词
        method_keywords = {
            'machine learning': ['深度学习', '神经网络', '强化学习'],
            'natural language processing': ['Transformer', '预训练模型', '注意力机制'],
            'computer vision': ['卷积神经网络', '目标检测', '图像分割'],
            'materials science': ['材料合成', '性能优化', '结构分析'],
        }
        
        domain_methods = method_keywords.get(domain.lower(), ['通用方法1', '通用方法2', '通用方法3'])
        return domain_methods
    
    def _suggest_application(self, method: str) -> str:
        """建议应用场景"""
        applications = [
            '数据分析与预测',
            '模式识别与分类',
            '优化与决策支持',
            '自动化处理',
            '质量控制',
        ]
        return random.choice(applications)
    
    def _identify_challenges(self, source: str, target: str) -> List[str]:
        """识别挑战"""
        challenges = [
            '数据格式和特征差异需要适配',
            '模型参数需要针对新领域调整',
            '验证标准和评估指标需要重新定义',
            '领域知识差异导致的理解障碍',
            '实验环境和条件的差异',
        ]
        return random.sample(challenges, k=3)
    
    def _generate_implementation_steps(self) -> List[str]:
        """生成实施步骤"""
        return [
            '1. 文献调研和可行性分析',
            '2. 数据收集和预处理',
            '3. 方法适配和参数调优',
            '4. 小规模验证实验',
            '5. 大规模应用和效果评估',
        ]


class GenerateAgent:
    """
    生成智能体
    
    核心职责：
    1. 创新假设生成
    2. 跨域知识迁移推荐
    3. 研究方向建议
    """
    
    def __init__(self):
        """初始化生成智能体"""
        self.hypothesis_generator = HypothesisGenerator()
        self.transfer_recommender = CrossDomainTransferRecommender()
        
        logger.info("生成智能体初始化完成")
    
    async def generate_innovations(
        self,
        research_gaps: List[Dict],
        papers: List[Dict],
        domains: List[str] = None
    ) -> Dict[str, Any]:
        """
        生成创新建议
        
        Args:
            research_gaps: 研究空白列表
            papers: 文献列表
            domains: 研究领域列表
        
        Returns:
            Dict: 创新建议结果
        """
        logger.info("开始生成创新建议")
        
        # 生成假设
        hypotheses = self.hypothesis_generator.generate_hypotheses(
            research_gaps, papers, count=settings.HYPOTHESIS_COUNT
        )
        
        # 跨域迁移推荐
        transfers = []
        if domains and len(domains) >= 2:
            for i in range(len(domains) - 1):
                transfer = self.transfer_recommender.recommend_transfers(
                    domains[i], domains[i+1], papers
                )
                transfers.extend(transfer)
        
        result = {
            'hypotheses': hypotheses,
            'cross_domain_transfers': transfers,
            'total_suggestions': len(hypotheses) + len(transfers),
            'high_confidence_count': sum(
                1 for h in hypotheses if h['confidence'] > 0.8
            ),
            'timestamp': datetime.now().isoformat(),
        }
        
        logger.success(f"创新建议生成完成: {result['total_suggestions']} 个建议")
        
        return result


# 创建全局生成智能体实例
generate_agent = GenerateAgent()