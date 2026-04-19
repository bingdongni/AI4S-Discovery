#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
评估智能体（Evaluate Agent）
负责技术成熟度（TRL）评估和技术可行性分析
"""

import asyncio
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger
import numpy as np
from collections import Counter, defaultdict

from src.core.config import settings


class EvaluateAgent:
    """评估智能体"""

    # TRL等级定义
    TRL_LEVELS = {
        1: "基础原理观察和报告",
        2: "技术概念和/或应用形成",
        3: "分析和实验性关键功能和/或特征的验证",
        4: "实验室环境中的组件和/或系统验证",
        5: "相关环境中的组件和/或系统验证",
        6: "相关环境中的系统/子系统模型或原型演示",
        7: "运行环境中的系统原型演示",
        8: "实际系统完成并通过测试和演示",
        9: "实际系统在运行环境中经过成功的任务运行证明",
    }

    # TRL关键词映射 - 扩展和优化
    TRL_KEYWORDS = {
        1: [
            'theory', 'principle', 'observation', 'basic', 'fundamental', 'concept',
            'hypothesis', 'theoretical', 'speculation', 'observed', 'phenomenon',
            'discover', 'identify', 'characterize', 'understand', 'explore'
        ],
        2: [
            'concept', 'application', 'formulation', 'hypothesis', 'theoretical',
            'propose', 'suggest', 'idea', 'framework', 'model', 'paradigm',
            'proof-of-concept', 'preliminary', 'initial', 'exploratory'
        ],
        3: [
            'experiment', 'proof', 'validation', 'laboratory', 'analytical',
            'simulation', 'test', 'demonstrate', 'verify', 'evaluate',
            'feasibility', 'prototype', 'lab', 'bench', 'controlled'
        ],
        4: [
            'component', 'laboratory', 'validation', 'prototype', 'bench', 'test',
            'integration', 'module', 'subsystem', 'functional', 'performance',
            'specification', 'requirement', 'engineering', 'prototype demonstration'
        ],
        5: [
            'relevant environment', 'integration', 'testing', 'demonstration',
            'field', 'operational', 'real-world', 'pilot', 'application',
            'end-to-end', 'system-level', 'interface', 'compatibility'
        ],
        6: [
            'prototype', 'demonstration', 'relevant environment', 'model',
            'engineering', 'system', 'breadboard', 'integration testing',
            'qualification', 'technology demonstration', 'representative'
        ],
        7: [
            'operational environment', 'prototype', 'demonstration', 'field test',
            'in-situ', 'deploy', 'trial', 'beta', 'pilot study', 'case study',
            'real application', 'working prototype', 'functional prototype'
        ],
        8: [
            'system', 'qualified', 'demonstrated', 'operational', 'complete',
            'tested', 'verified', 'validated', 'certified', 'production',
            'manufacturing', 'commercialization', 'flight test', 'launch'
        ],
        9: [
            'operational', 'proven', 'successful', 'deployment', 'commercial',
            'production', 'market', 'mass production', 'routine', 'reliable',
            'established', 'mature', 'standard', 'widely adopted', 'deployed'
        ]
    }

    # 高影响力期刊/会议列表（用于TRL推断）
    HIGH_IMPACT_VENUES = {
        # 顶级期刊
        'nature': 9, 'science': 9, 'cell': 9,
        # 高影响力期刊
        'nature medicine': 8, 'lancet': 8, 'science translational medicine': 8,
        # 专业顶级期刊
        'physical review': 7, 'nature physics': 8, 'nature materials': 8,
        # AI/ML顶级会议
        'neurips': 7, 'icml': 7, 'iclr': 7,
        'aaai': 6, 'ijcai': 6,
        # 通用高影响力
        'ieee': 6, 'acm': 6, 'springer': 5
    }

    def __init__(self):
        """初始化评估智能体"""
        logger.info("评估智能体初始化完成")

    async def assess_trl(
        self,
        papers: List[Dict],
        query: str,
        analysis_results: Optional[Dict] = None,
    ) -> Dict:
        """
        评估技术成熟度（TRL）

        Args:
            papers: 文献列表
            query: 研究查询
            analysis_results: 分析结果（可选）

        Returns:
            Dict: TRL评估结果
        """
        logger.info(f"开始TRL评估，文献数: {len(papers)}")

        if not papers or len(papers) == 0:
            return self._empty_result()

        # 1. 基于关键词的TRL评估
        keyword_scores = self._assess_by_keywords(papers)

        # 2. 基于实验阶段的TRL评估
        experiment_scores = self._assess_by_experiment_stage(papers)

        # 3. 基于引用和影响力的TRL评估
        citation_scores = self._assess_by_citations(papers)

        # 4. 基于发表 venues 的TRL评估
        venue_scores = self._assess_by_venue(papers)

        # 5. 基于时间演进的TRL评估
        temporal_scores = self._assess_by_temporal_evolution(papers)

        # 6. 综合评分
        final_level, confidence, scoring_details = self._calculate_final_trl(
            keyword_scores, experiment_scores, citation_scores,
            venue_scores, temporal_scores, papers
        )

        # 7. 收集证据
        evidence = self._collect_evidence(papers, final_level)

        # 8. 分析TRL分布
        distribution = self._analyze_trl_distribution(
            keyword_scores, experiment_scores, citation_scores,
            venue_scores, temporal_scores
        )

        # 9. 分析TRL趋势
        trend = self._analyze_trl_trend(papers, temporal_scores)

        result = {
            'level': final_level,
            'confidence': confidence,
            'level_description': self.TRL_LEVELS.get(final_level, '未知'),
            'evidence': evidence,
            'distribution': distribution,
            'trend': trend,
            'scoring_details': scoring_details,
            'assessment_method': 'multi_factor_analysis',
            'assessment_date': datetime.now().isoformat(),
        }

        logger.success(f"TRL评估完成: Level {final_level} (置信度: {confidence:.2%})")
        return result

    def _empty_result(self) -> Dict:
        """返回空结果"""
        return {
            'level': 0,
            'confidence': 0.0,
            'level_description': '数据不足，无法评估',
            'evidence': [],
            'distribution': {},
            'trend': {},
            'assessment_method': 'multi_factor_analysis',
            'assessment_date': datetime.now().isoformat(),
        }

    def _extract_text(self, paper: Dict) -> str:
        """从论文中提取可分析的文本"""
        text_parts = []

        # 标题
        if paper.get('title'):
            text_parts.append(paper['title'])

        # 摘要
        if paper.get('abstract'):
            text_parts.append(paper['abstract'])

        # 期刊/会议
        if paper.get('journal'):
            text_parts.append(paper['journal'])
        if paper.get('venue'):
            text_parts.append(paper['venue'])

        # 合并并转小写
        text = ' '.join(text_parts).lower()

        # 移除特殊字符但保留空格和字母数字
        text = re.sub(r'[^a-z0-9\s]', ' ', text)

        return text

    def _assess_by_keywords(self, papers: List[Dict]) -> Dict[int, float]:
        """基于关键词评估TRL"""
        trl_scores = {level: 0.0 for level in range(1, 10)}

        for paper in papers:
            text = self._extract_text(paper)
            quality_weight = self._get_quality_weight(paper)

            for level, keywords in self.TRL_KEYWORDS.items():
                matches = sum(1 for kw in keywords if kw in text)

                if matches > 0:
                    # 根据匹配数量和质量加权
                    trl_scores[level] += matches * quality_weight

        # 归一化
        total = sum(trl_scores.values())
        if total > 0:
            trl_scores = {k: v / total for k, v in trl_scores.items()}

        return trl_scores

    def _get_quality_weight(self, paper: Dict) -> float:
        """根据论文质量计算权重"""
        weight = 1.0

        # 引用数加权
        citations = paper.get('citationCount', 0) or paper.get('citations', 0)
        if citations:
            if citations > 100:
                weight *= 2.0
            elif citations > 50:
                weight *= 1.5
            elif citations > 10:
                weight *= 1.2

        # 质量分数加权
        quality_score = paper.get('quality_score', 0)
        if quality_score:
            weight *= (1 + quality_score / 100)

        return weight

    def _assess_by_experiment_stage(self, papers: List[Dict]) -> Dict[int, float]:
        """基于实验阶段评估TRL"""
        stage_keywords = {
            'theoretical': [1, 2, 3],
            'laboratory': [3, 4, 5],
            'prototype': [5, 6, 7],
            'operational': [7, 8, 9],
            'commercial': [8, 9],
            'simulation': [3, 4],
            'numerical': [3, 4],
            'computational': [3, 4, 5],
            'experimental': [3, 4, 5],
            'clinical': [6, 7, 8, 9],
            'field': [6, 7],
            'deployment': [8, 9],
        }

        trl_scores = {level: 0.0 for level in range(1, 10)}

        for paper in papers:
            text = self._extract_text(paper)
            quality_weight = self._get_quality_weight(paper)

            for stage, levels in stage_keywords.items():
                if stage in text:
                    for level in levels:
                        trl_scores[level] += quality_weight

        # 归一化
        total = sum(trl_scores.values())
        if total > 0:
            trl_scores = {k: v / total for k, v in trl_scores.items()}

        return trl_scores

    def _assess_by_citations(self, papers: List[Dict]) -> Dict[int, float]:
        """基于引用数量评估TRL"""
        trl_scores = {level: 0.0 for level in range(1, 10)}

        # 按引用数分组
        citation_groups = {
            (0, 5): [1, 2],      # 很少引用 -> 早期阶段
            (5, 20): [3, 4],     # 少量引用 -> 实验室验证
            (20, 50): [4, 5, 6], # 中等引用 -> 应用验证
            (50, 100): [6, 7],   # 较多引用 -> 工业验证
            (100, float('inf')): [7, 8, 9],  # 高引用 -> 商业化
        }

        for paper in papers:
            citations = paper.get('citationCount', 0) or paper.get('citations', 0)
            quality_weight = self._get_quality_weight(paper)

            for (min_c, max_c), levels in citation_groups.items():
                if min_c <= citations < max_c:
                    for level in levels:
                        # 引用越多，越倾向于高TRL
                        proximity_bonus = 1.0 + (citations - min_c) / (max_c - min_c + 1) * 0.5
                        trl_scores[level] += quality_weight * proximity_bonus
                    break

        # 归一化
        total = sum(trl_scores.values())
        if total > 0:
            trl_scores = {k: v / total for k, v in trl_scores.items()}

        return trl_scores

    def _assess_by_venue(self, papers: List[Dict]) -> Dict[int, float]:
        """基于发表 venue 评估TRL"""
        trl_scores = {level: 0.0 for level in range(1, 10)}

        for paper in papers:
            venue = ''
            if paper.get('journal'):
                venue = paper['journal'].lower()
            elif paper.get('venue'):
                venue = paper['venue'].lower()

            quality_weight = self._get_quality_weight(paper)

            # 检查是否匹配高影响力venue
            matched_level = 0
            for pattern, level in self.HIGH_IMPACT_VENUES.items():
                if pattern in venue:
                    matched_level = max(matched_level, level)

            if matched_level > 0:
                # 直接赋值高TRL
                trl_scores[matched_level] += quality_weight * 2

                # 周围等级也有一定分数
                for offset in [-1, 1]:
                    neighbor_level = matched_level + offset
                    if 1 <= neighbor_level <= 9:
                        trl_scores[neighbor_level] += quality_weight * 0.5

        # 归一化
        total = sum(trl_scores.values())
        if total > 0:
            trl_scores = {k: v / total for k, v in trl_scores.items()}

        return trl_scores

    def _assess_by_temporal_evolution(self, papers: List[Dict]) -> Dict[int, float]:
        """基于时间演进评估TRL"""
        # 按年份分组
        papers_by_year = defaultdict(list)
        for paper in papers:
            year = paper.get('year')
            if year:
                papers_by_year[year].append(paper)

        if not papers_by_year:
            return {level: 0.0 for level in range(1, 10)}

        # 计算年份范围和趋势
        years = sorted(papers_by_year.keys())
        year_range = max(years) - min(years) + 1 if len(years) > 1 else 1
        current_year = datetime.now().year
        recent_years = max(years) >= current_year - 2

        trl_scores = {level: 0.0 for level in range(1, 10)}

        # 计算每年对应的平均引用/影响力
        for year in years:
            year_papers = papers_by_year[year]
            avg_quality = np.mean([self._get_quality_weight(p) for p in year_papers])

            # 计算年份对应的TRL倾向
            # 假设：早期研究TRL较低(1-3)，近期研究TRL较高(5-9)
            year_progress = (year - min(years)) / max(year_range, 1)

            # 根据是否最近2年调整
            if recent_years:
                expected_trl_base = 1 + year_progress * 6  # 1-7范围
            else:
                expected_trl_base = 1 + year_progress * 8  # 1-9范围

            # 为该年份的文献分配TRL分数
            for paper in year_papers:
                quality_weight = self._get_quality_weight(paper)

                # 在expected_trl附近的等级获得更高分数
                for level in range(1, 10):
                    distance = abs(level - expected_trl_base)
                    score = max(0, 1 - distance / 4) * quality_weight
                    trl_scores[level] += score

        # 归一化
        total = sum(trl_scores.values())
        if total > 0:
            trl_scores = {k: v / total for k, v in trl_scores.items()}

        return trl_scores

    def _calculate_final_trl(
        self,
        keyword_scores: Dict[int, float],
        experiment_scores: Dict[int, float],
        citation_scores: Dict[int, float],
        venue_scores: Dict[int, float],
        temporal_scores: Dict[int, float],
        papers: List[Dict]
    ) -> Tuple[int, float, Dict]:
        """计算最终TRL等级和置信度"""
        # 综合权重
        weights = {
            'keyword': 0.25,
            'experiment': 0.20,
            'citation': 0.20,
            'venue': 0.15,
            'temporal': 0.20,
        }

        combined_scores = {}
        for level in range(1, 10):
            combined_scores[level] = (
                keyword_scores.get(level, 0) * weights['keyword'] +
                experiment_scores.get(level, 0) * weights['experiment'] +
                citation_scores.get(level, 0) * weights['citation'] +
                venue_scores.get(level, 0) * weights['venue'] +
                temporal_scores.get(level, 0) * weights['temporal']
            )

        # 找到得分最高的等级
        max_level = max(combined_scores.items(), key=lambda x: x[1])[0]
        max_score = combined_scores[max_level]

        # 考虑相邻等级的支持
        neighbor_support = 0
        for level in range(1, 10):
            if abs(level - max_level) == 1:
                neighbor_support += combined_scores[level] * 0.5

        # 如果相邻等级有较强支持，可能需要调整
        if neighbor_support > max_score * 0.5:
            # 计算加权平均
            weighted_sum = sum(level * score for level, score in combined_scores.items())
            total_score = sum(combined_scores.values())
            if total_score > 0:
                final_level_float = weighted_sum / total_score
                # 四舍五入到整数
                final_level = round(final_level_float)
            else:
                final_level = max_level
        else:
            final_level = max_level

        # 确保在有效范围内
        final_level = max(1, min(9, final_level))

        # 计算置信度
        confidence = self._calculate_confidence(
            combined_scores, max_score, neighbor_support, len(papers)
        )

        scoring_details = {
            'combined_scores': {k: round(v, 4) for k, v in combined_scores.items()},
            'weights': weights,
            'max_level': max_level,
            'neighbor_support': round(neighbor_support, 4),
        }

        return final_level, confidence, scoring_details

    def _calculate_confidence(
        self,
        combined_scores: Dict[int, float],
        max_score: float,
        neighbor_support: float,
        paper_count: int
    ) -> float:
        """计算评估置信度"""
        # 基础置信度
        total_score = sum(combined_scores.values())
        if total_score > 0:
            base_confidence = max_score / total_score
        else:
            base_confidence = 0

        # 分散度惩罚
        score_std = np.std(list(combined_scores.values()))
        distribution_penalty = min(score_std * 2, 0.3)

        # 样本数量加成
        if paper_count >= 100:
            sample_bonus = 0.15
        elif paper_count >= 50:
            sample_bonus = 0.10
        elif paper_count >= 20:
            sample_bonus = 0.05
        else:
            sample_bonus = 0

        # 综合置信度
        confidence = base_confidence - distribution_penalty + sample_bonus

        # 确保在合理范围内
        confidence = max(0.1, min(0.99, confidence))

        # 应用TRL阈值
        confidence = max(settings.TRL_CONFIDENCE_THRESHOLD, confidence)

        return round(confidence, 4)

    def _collect_evidence(self, papers: List[Dict], trl_level: int) -> List[Dict]:
        """收集支持TRL评估的证据"""
        evidence = []
        keywords = self.TRL_KEYWORDS.get(trl_level, [])

        # 按质量分数排序
        sorted_papers = sorted(
            papers,
            key=lambda x: x.get('quality_score', 0) + x.get('citationCount', 0),
            reverse=True
        )

        for paper in sorted_papers[:20]:  # 检查前20篇高质量文献
            text = self._extract_text(paper)
            matches = [kw for kw in keywords if kw in text]

            if matches:
                evidence.append({
                    'title': paper.get('title', '')[:100],
                    'year': paper.get('year'),
                    'quality_score': paper.get('quality_score', 0),
                    'citation_count': paper.get('citationCount', 0) or paper.get('citations', 0),
                    'matched_keywords': matches[:5],
                    'abstract_snippet': paper.get('abstract', '')[:200] if paper.get('abstract') else '',
                    'journal': paper.get('journal', '') or paper.get('venue', ''),
                })

        # 按质量分数排序，返回前5个
        evidence.sort(key=lambda x: x['quality_score'], reverse=True)
        return evidence[:5]

    def _analyze_trl_distribution(
        self,
        keyword_scores: Dict[int, float],
        experiment_scores: Dict[int, float],
        citation_scores: Dict[int, float],
        venue_scores: Dict[int, float],
        temporal_scores: Dict[int, float]
    ) -> Dict:
        """分析TRL分布"""
        distribution = {}

        weights = {
            'keyword': 0.25,
            'experiment': 0.20,
            'citation': 0.20,
            'venue': 0.15,
            'temporal': 0.20,
        }

        for level in range(1, 10):
            combined_score = (
                keyword_scores.get(level, 0) * weights['keyword'] +
                experiment_scores.get(level, 0) * weights['experiment'] +
                citation_scores.get(level, 0) * weights['citation'] +
                venue_scores.get(level, 0) * weights['venue'] +
                temporal_scores.get(level, 0) * weights['temporal']
            )

            distribution[level] = {
                'score': round(combined_score, 4),
                'percentage': round(combined_score * 100, 2),
                'description': self.TRL_LEVELS.get(level, ''),
            }

        return distribution

    def _analyze_trl_trend(
        self,
        papers: List[Dict],
        temporal_scores: Dict[int, float]
    ) -> Dict:
        """分析TRL趋势"""
        # 按年份分组
        papers_by_year = defaultdict(list)
        for paper in papers:
            year = paper.get('year')
            if year:
                papers_by_year[year].append(paper)

        if not papers_by_year:
            return {'trend': 'insufficient_data', 'yearly_trl': {}}

        # 计算每年的平均引用/影响力
        yearly_trl = {}
        for year in sorted(papers_by_year.keys()):
            year_papers = papers_by_year[year]
            avg_quality = np.mean([self._get_quality_weight(p) for p in year_papers])

            # 粗略估算每年的TRL
            year_trl = 1 + (avg_quality - 1) * 0.8
            year_trl = max(1, min(9, year_trl))
            yearly_trl[year] = round(year_trl, 2)

        # 判断趋势
        years = sorted(yearly_trl.keys())
        if len(years) < 2:
            return {
                'trend': 'insufficient_data',
                'yearly_trl': yearly_trl,
                'current_trl': yearly_trl.get(max(years), 0) if years else 0
            }

        # 线性回归判断趋势
        from scipy.stats import linregress
        x = list(range(len(years)))
        y = [yearly_trl[y] for y in years]
        slope, intercept, r_value, p_value, std_err = linregress(x, y)

        if slope > 0.3:
            trend = 'increasing'
        elif slope < -0.3:
            trend = 'decreasing'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'yearly_trl': yearly_trl,
            'current_trl': yearly_trl.get(max(years), 0),
            'slope': round(slope, 4),
            'r_squared': round(r_value ** 2, 4),
        }

    def assess_feasibility(
        self,
        trl_result: Dict,
        analysis_results: Optional[Dict] = None,
    ) -> Dict:
        """
        评估技术可行性

        Args:
            trl_result: TRL评估结果
            analysis_results: 分析结果

        Returns:
            Dict: 可行性评估
        """
        trl_level = trl_result.get('level', 0)
        confidence = trl_result.get('confidence', 0)

        # 基于TRL等级判断可行性
        if trl_level >= 7:
            feasibility = 'high'
            recommendation = '技术已接近或达到商业化阶段，建议加速推进'
            timeline = '3-12个月可进入市场'
        elif trl_level >= 4:
            feasibility = 'medium'
            recommendation = '技术处于验证阶段，建议继续研发和测试'
            timeline = '1-3年可商业化'
        elif trl_level >= 2:
            feasibility = 'low'
            recommendation = '技术处于早期阶段，需要大量基础研究'
            timeline = '3-5年以上才能商业化'
        else:
            feasibility = 'very_low'
            recommendation = '技术概念尚未成熟，建议谨慎投入'
            timeline = '不确定，需要先验证基础原理'

        # 考虑置信度
        if confidence < 0.6:
            feasibility += '_uncertain'
            recommendation += '（评估置信度较低，建议进一步调研）'

        # 风险评估
        risk_level = self._assess_risk_level(trl_level, confidence)

        # 资源需求估算
        resource_estimate = self._estimate_resources(trl_level)

        return {
            'feasibility': feasibility,
            'recommendation': recommendation,
            'timeline': timeline,
            'trl_level': trl_level,
            'confidence': confidence,
            'risk_level': risk_level,
            'resource_estimate': resource_estimate,
        }

    def _assess_risk_level(self, trl_level: int, confidence: float) -> str:
        """评估风险等级"""
        if trl_level >= 7 and confidence >= 0.8:
            return 'low'
        elif trl_level >= 4 and confidence >= 0.6:
            return 'medium'
        elif trl_level >= 2:
            return 'high'
        else:
            return 'very_high'

    def _estimate_resources(self, trl_level: int) -> Dict:
        """估算所需资源"""
        resource_tiers = {
            (1, 2): {
                'funding': '$50K-200K',
                'team_size': '2-5人',
                'duration': '6-18个月',
                'equipment': '基本计算资源',
                'difficulty': '低'
            },
            (3, 4): {
                'funding': '$200K-1M',
                'team_size': '5-10人',
                'duration': '1-3年',
                'equipment': '实验设备、高性能计算',
                'difficulty': '中'
            },
            (5, 6): {
                'funding': '$1M-5M',
                'team_size': '10-30人',
                'duration': '2-5年',
                'equipment': '专业设备、中试产线',
                'difficulty': '中高'
            },
            (7, 9): {
                'funding': '$5M-50M',
                'team_size': '30-100+人',
                'duration': '3-10年',
                'equipment': '生产线、认证设备',
                'difficulty': '高'
            }
        }

        for (min_level, max_level), resources in resource_tiers.items():
            if min_level <= trl_level <= max_level:
                return resources

        return {
            'funding': '不确定',
            'team_size': '不确定',
            'duration': '不确定',
            'equipment': '不确定',
            'difficulty': '高'
        }


# 创建全局评估智能体实例
evaluate_agent = EvaluateAgent()
