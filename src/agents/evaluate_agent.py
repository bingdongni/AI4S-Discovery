#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
评估智能体（Evaluate Agent）
负责技术成熟度（TRL）评估和技术可行性分析
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
import numpy as np
from collections import Counter

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
    
    # TRL关键词映射
    TRL_KEYWORDS = {
        1: ['theory', 'principle', 'observation', 'basic', 'fundamental', 'concept'],
        2: ['concept', 'application', 'formulation', 'hypothesis', 'theoretical'],
        3: ['experiment', 'proof', 'validation', 'laboratory', 'analytical', 'simulation'],
        4: ['component', 'laboratory', 'validation', 'prototype', 'bench', 'test'],
        5: ['relevant environment', 'integration', 'testing', 'demonstration'],
        6: ['prototype', 'demonstration', 'relevant environment', 'model', 'engineering'],
        7: ['operational environment', 'prototype', 'demonstration', 'field test'],
        8: ['system', 'qualified', 'demonstrated', 'operational', 'complete'],
        9: ['operational', 'proven', 'successful', 'deployment', 'commercial', 'production'],
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
        
        if not papers:
            return {
                'level': 0,
                'confidence': 0.0,
                'evidence': [],
                'distribution': {},
                'trend': {},
            }
        
        # 1. 基于关键词的TRL评估
        keyword_scores = self._assess_by_keywords(papers)
        
        # 2. 基于实验阶段的TRL评估
        experiment_scores = self._assess_by_experiment_stage(papers)
        
        # 3. 基于时间演进的TRL评估
        temporal_scores = self._assess_by_temporal_evolution(papers)
        
        # 4. 综合评分
        final_level, confidence = self._calculate_final_trl(
            keyword_scores,
            experiment_scores,
            temporal_scores
        )
        
        # 5. 收集证据
        evidence = self._collect_evidence(papers, final_level)
        
        # 6. 分析TRL分布
        distribution = self._analyze_trl_distribution(
            keyword_scores,
            experiment_scores,
            temporal_scores
        )
        
        # 7. 分析TRL趋势
        trend = self._analyze_trl_trend(papers, temporal_scores)
        
        result = {
            'level': final_level,
            'confidence': confidence,
            'level_description': self.TRL_LEVELS.get(final_level, '未知'),
            'evidence': evidence,
            'distribution': distribution,
            'trend': trend,
            'assessment_date': datetime.now().isoformat(),
        }
        
        logger.success(f"TRL评估完成: Level {final_level} (置信度: {confidence:.2%})")
        return result
    
    def _assess_by_keywords(self, papers: List[Dict]) -> Dict[int, float]:
        """基于关键词评估TRL"""
        trl_scores = {level: 0.0 for level in range(1, 10)}
        
        for paper in papers:
            # 提取文本
            text = ' '.join([
                paper.get('title', ''),
                paper.get('abstract', ''),
            ]).lower()
            
            # 计算每个TRL等级的匹配度
            for level, keywords in self.TRL_KEYWORDS.items():
                matches = sum(1 for kw in keywords if kw in text)
                if matches > 0:
                    # 根据文献质量加权
                    weight = paper.get('quality_score', 50) / 100
                    trl_scores[level] += matches * weight
        
        # 归一化
        total = sum(trl_scores.values())
        if total > 0:
            trl_scores = {k: v / total for k, v in trl_scores.items()}
        
        return trl_scores
    
    def _assess_by_experiment_stage(self, papers: List[Dict]) -> Dict[int, float]:
        """基于实验阶段评估TRL"""
        stage_keywords = {
            'theoretical': [1, 2, 3],
            'laboratory': [3, 4, 5],
            'prototype': [5, 6, 7],
            'operational': [7, 8, 9],
            'commercial': [8, 9],
        }
        
        trl_scores = {level: 0.0 for level in range(1, 10)}
        
        for paper in papers:
            text = ' '.join([
                paper.get('title', ''),
                paper.get('abstract', ''),
            ]).lower()
            
            for stage, levels in stage_keywords.items():
                if stage in text:
                    weight = paper.get('quality_score', 50) / 100
                    for level in levels:
                        trl_scores[level] += weight
        
        # 归一化
        total = sum(trl_scores.values())
        if total > 0:
            trl_scores = {k: v / total for k, v in trl_scores.items()}
        
        return trl_scores
    
    def _assess_by_temporal_evolution(self, papers: List[Dict]) -> Dict[int, float]:
        """基于时间演进评估TRL"""
        # 按年份分组
        papers_by_year = {}
        for paper in papers:
            year = paper.get('year')
            if year:
                if year not in papers_by_year:
                    papers_by_year[year] = []
                papers_by_year[year].append(paper)
        
        if not papers_by_year:
            return {level: 0.0 for level in range(1, 10)}
        
        # 假设：早期研究TRL较低，近期研究TRL较高
        years = sorted(papers_by_year.keys())
        year_range = max(years) - min(years) + 1
        
        trl_scores = {level: 0.0 for level in range(1, 10)}
        
        for year in years:
            # 计算年份对应的TRL倾向（线性增长）
            year_progress = (year - min(years)) / max(year_range, 1)
            expected_trl = 1 + year_progress * 8  # 1-9的范围
            
            # 为该年份的文献分配TRL分数
            for paper in papers_by_year[year]:
                weight = paper.get('quality_score', 50) / 100
                
                # 在expected_trl附近的等级获得更高分数
                for level in range(1, 10):
                    distance = abs(level - expected_trl)
                    score = max(0, 1 - distance / 3) * weight  # 距离越近分数越高
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
        temporal_scores: Dict[int, float],
    ) -> tuple:
        """计算最终TRL等级和置信度"""
        # 综合三种评估方法（加权平均）
        weights = {
            'keyword': 0.4,
            'experiment': 0.3,
            'temporal': 0.3,
        }
        
        combined_scores = {}
        for level in range(1, 10):
            combined_scores[level] = (
                keyword_scores.get(level, 0) * weights['keyword'] +
                experiment_scores.get(level, 0) * weights['experiment'] +
                temporal_scores.get(level, 0) * weights['temporal']
            )
        
        # 找到得分最高的等级
        final_level = max(combined_scores.items(), key=lambda x: x[1])[0]
        
        # 计算置信度（基于得分分布的集中程度）
        max_score = combined_scores[final_level]
        total_score = sum(combined_scores.values())
        
        if total_score > 0:
            confidence = max_score / total_score
            
            # 如果得分分布过于分散，降低置信度
            score_std = np.std(list(combined_scores.values()))
            if score_std > 0.1:
                confidence *= 0.8
        else:
            confidence = 0.0
        
        # 确保置信度在合理范围内
        confidence = max(settings.TRL_CONFIDENCE_THRESHOLD, min(1.0, confidence))
        
        return final_level, confidence
    
    def _collect_evidence(self, papers: List[Dict], trl_level: int) -> List[Dict]:
        """收集支持TRL评估的证据"""
        evidence = []
        keywords = self.TRL_KEYWORDS.get(trl_level, [])
        
        # 找到包含相关关键词的高质量文献
        for paper in papers:
            text = ' '.join([
                paper.get('title', ''),
                paper.get('abstract', ''),
            ]).lower()
            
            matches = [kw for kw in keywords if kw in text]
            
            if matches and paper.get('quality_score', 0) >= 60:
                evidence.append({
                    'title': paper.get('title', ''),
                    'year': paper.get('year'),
                    'quality_score': paper.get('quality_score', 0),
                    'matched_keywords': matches,
                    'abstract_snippet': paper.get('abstract', '')[:200],
                })
        
        # 按质量分数排序，返回前5个
        evidence.sort(key=lambda x: x['quality_score'], reverse=True)
        return evidence[:5]
    
    def _analyze_trl_distribution(
        self,
        keyword_scores: Dict[int, float],
        experiment_scores: Dict[int, float],
        temporal_scores: Dict[int, float],
    ) -> Dict:
        """分析TRL分布"""
        distribution = {}
        
        for level in range(1, 10):
            avg_score = (
                keyword_scores.get(level, 0) +
                experiment_scores.get(level, 0) +
                temporal_scores.get(level, 0)
            ) / 3
            
            distribution[level] = {
                'score': round(avg_score, 4),
                'percentage': round(avg_score * 100, 2),
                'description': self.TRL_LEVELS.get(level, ''),
            }
        
        return distribution
    
    def _analyze_trl_trend(
        self,
        papers: List[Dict],
        temporal_scores: Dict[int, float],
    ) -> Dict:
        """分析TRL趋势"""
        # 按年份分组并计算平均TRL
        papers_by_year = {}
        for paper in papers:
            year = paper.get('year')
            if year:
                if year not in papers_by_year:
                    papers_by_year[year] = []
                papers_by_year[year].append(paper)
        
        if not papers_by_year:
            return {'trend': 'unknown', 'yearly_trl': {}}
        
        # 计算每年的平均TRL
        yearly_trl = {}
        for year in sorted(papers_by_year.keys()):
            # 简化：使用temporal_scores的加权平均
            avg_trl = sum(
                level * score
                for level, score in temporal_scores.items()
            )
            yearly_trl[year] = round(avg_trl, 2)
        
        # 判断趋势
        years = sorted(yearly_trl.keys())
        if len(years) >= 2:
            first_half_avg = np.mean([yearly_trl[y] for y in years[:len(years)//2]])
            second_half_avg = np.mean([yearly_trl[y] for y in years[len(years)//2:]])
            
            if second_half_avg > first_half_avg + 0.5:
                trend = 'increasing'
            elif second_half_avg < first_half_avg - 0.5:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'trend': trend,
            'yearly_trl': yearly_trl,
            'current_trl': yearly_trl.get(max(years), 0) if years else 0,
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
        elif trl_level >= 4:
            feasibility = 'medium'
            recommendation = '技术处于验证阶段，建议继续研发和测试'
        elif trl_level >= 2:
            feasibility = 'low'
            recommendation = '技术处于早期阶段，需要大量基础研究'
        else:
            feasibility = 'very_low'
            recommendation = '技术概念尚未成熟，建议谨慎投入'
        
        # 考虑置信度
        if confidence < 0.6:
            feasibility += '_uncertain'
            recommendation += '（评估置信度较低，建议进一步调研）'
        
        return {
            'feasibility': feasibility,
            'recommendation': recommendation,
            'trl_level': trl_level,
            'confidence': confidence,
            'risk_level': self._assess_risk_level(trl_level, confidence),
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


# 创建全局评估智能体实例
evaluate_agent = EvaluateAgent()
