#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析智能体（Analysis Agent）
负责文献质量评分、关键信息提取和趋势分析
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
import numpy as np

from src.core.config import settings


class PaperQualityScorer:
    """文献质量评分器"""
    
    def __init__(self):
        """初始化评分器"""
        self.weights = {
            'citation_count': 0.25,
            'venue_quality': 0.20,
            'author_reputation': 0.15,
            'recency': 0.15,
            'completeness': 0.15,
            'reproducibility': 0.10,
        }
    
    def score_paper(self, paper: Dict) -> float:
        """
        评分单篇文献
        
        Args:
            paper: 文献信息字典
        
        Returns:
            float: 质量分数 (0-100)
        """
        scores = {}
        
        # 1. 引用数评分
        citation_count = paper.get('citationCount', 0)
        scores['citation_count'] = min(citation_count / 100, 1.0) * 100
        
        # 2. 发表venue质量评分
        venue = paper.get('venue', '').lower()
        scores['venue_quality'] = self._score_venue(venue)
        
        # 3. 作者声誉评分
        authors = paper.get('authors', [])
        scores['author_reputation'] = self._score_authors(authors)
        
        # 4. 时效性评分
        year = paper.get('year', 0)
        scores['recency'] = self._score_recency(year)
        
        # 5. 完整性评分
        scores['completeness'] = self._score_completeness(paper)
        
        # 6. 可复现性评分
        scores['reproducibility'] = self._score_reproducibility(paper)
        
        # 加权总分
        total_score = sum(
            scores[key] * self.weights[key]
            for key in self.weights.keys()
        )
        
        return round(total_score, 2)
    
    def _score_venue(self, venue: str) -> float:
        """评分发表venue"""
        # 顶级会议和期刊
        top_venues = [
            'nature', 'science', 'cell', 'nejm', 'lancet',
            'neurips', 'icml', 'iclr', 'cvpr', 'iccv',
            'acl', 'emnlp', 'naacl', 'sigir', 'kdd',
            'jacs', 'advanced materials', 'energy'
        ]
        
        for top in top_venues:
            if top in venue:
                return 100.0
        
        # 一般期刊/会议
        if any(word in venue for word in ['journal', 'conference', 'proceedings']):
            return 70.0
        
        # 预印本
        if 'arxiv' in venue or 'biorxiv' in venue:
            return 50.0
        
        return 40.0
    
    def _score_authors(self, authors: List[Dict]) -> float:
        """评分作者团队"""
        if not authors:
            return 50.0
        
        # 简化版：基于作者数量和h-index（如果有）
        author_count = len(authors)
        
        # 理想作者数：3-8人
        if 3 <= author_count <= 8:
            count_score = 100.0
        elif author_count < 3:
            count_score = 60.0
        else:
            count_score = max(100.0 - (author_count - 8) * 5, 50.0)
        
        return count_score
    
    def _score_recency(self, year: int) -> float:
        """评分时效性"""
        if year == 0:
            return 50.0
        
        current_year = datetime.now().year
        age = current_year - year
        
        if age <= 1:
            return 100.0
        elif age <= 3:
            return 90.0
        elif age <= 5:
            return 75.0
        elif age <= 10:
            return 60.0
        else:
            return max(50.0 - (age - 10) * 2, 20.0)
    
    def _score_completeness(self, paper: Dict) -> float:
        """评分完整性"""
        score = 0.0
        
        # 有标题
        if paper.get('title'):
            score += 20.0
        
        # 有摘要
        if paper.get('abstract'):
            score += 30.0
        
        # 有作者
        if paper.get('authors'):
            score += 20.0
        
        # 有发表信息
        if paper.get('venue') or paper.get('year'):
            score += 15.0
        
        # 有引用信息
        if 'citationCount' in paper:
            score += 15.0
        
        return score
    
    def _score_reproducibility(self, paper: Dict) -> float:
        """评分可复现性"""
        score = 50.0  # 基础分
        
        abstract = paper.get('abstract', '').lower()
        
        # 包含方法描述
        if any(word in abstract for word in ['method', 'algorithm', 'approach', 'technique']):
            score += 15.0
        
        # 包含数据集信息
        if any(word in abstract for word in ['dataset', 'data', 'benchmark']):
            score += 15.0
        
        # 包含代码/实现信息
        if any(word in abstract for word in ['code', 'implementation', 'github', 'open source']):
            score += 20.0
        
        return min(score, 100.0)


class KeyInformationExtractor:
    """关键信息提取器"""
    
    def extract(self, paper: Dict) -> Dict[str, Any]:
        """
        提取文献关键信息
        
        Args:
            paper: 文献信息
        
        Returns:
            Dict: 提取的关键信息
        """
        return {
            'title': paper.get('title', ''),
            'authors': self._extract_author_names(paper.get('authors', [])),
            'year': paper.get('year', 0),
            'venue': paper.get('venue', ''),
            'abstract': paper.get('abstract', ''),
            'keywords': self._extract_keywords(paper),
            'methods': self._extract_methods(paper),
            'datasets': self._extract_datasets(paper),
            'metrics': self._extract_metrics(paper),
            'contributions': self._extract_contributions(paper),
        }
    
    def _extract_author_names(self, authors: List[Dict]) -> List[str]:
        """提取作者姓名"""
        names = []
        for author in authors:
            if isinstance(author, dict):
                name = author.get('name', '')
            else:
                name = str(author)
            if name:
                names.append(name)
        return names
    
    def _extract_keywords(self, paper: Dict) -> List[str]:
        """提取关键词"""
        # 简化版：从标题和摘要中提取
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        
        # 常见学术关键词模式
        keywords = []
        
        # 提取专业术语（大写开头的连续词）
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(pattern, text)
        keywords.extend(matches[:10])
        
        return list(set(keywords))
    
    def _extract_methods(self, paper: Dict) -> List[str]:
        """提取方法"""
        abstract = paper.get('abstract', '').lower()
        
        methods = []
        method_keywords = [
            'neural network', 'deep learning', 'machine learning',
            'transformer', 'cnn', 'rnn', 'lstm', 'gnn',
            'reinforcement learning', 'supervised learning',
            'unsupervised learning', 'transfer learning'
        ]
        
        for keyword in method_keywords:
            if keyword in abstract:
                methods.append(keyword)
        
        return methods
    
    def _extract_datasets(self, paper: Dict) -> List[str]:
        """提取数据集"""
        abstract = paper.get('abstract', '').lower()
        
        datasets = []
        dataset_keywords = [
            'imagenet', 'coco', 'mnist', 'cifar',
            'glue', 'squad', 'wmt', 'pubmed',
            'arxiv', 'wikipedia', 'common crawl'
        ]
        
        for keyword in dataset_keywords:
            if keyword in abstract:
                datasets.append(keyword.upper())
        
        return datasets
    
    def _extract_metrics(self, paper: Dict) -> List[str]:
        """提取评估指标"""
        abstract = paper.get('abstract', '').lower()
        
        metrics = []
        metric_keywords = [
            'accuracy', 'precision', 'recall', 'f1',
            'auc', 'map', 'bleu', 'rouge',
            'perplexity', 'loss', 'error rate'
        ]
        
        for keyword in metric_keywords:
            if keyword in abstract:
                metrics.append(keyword)
        
        return metrics
    
    def _extract_contributions(self, paper: Dict) -> List[str]:
        """提取主要贡献"""
        abstract = paper.get('abstract', '')
        
        # 简化版：查找包含贡献关键词的句子
        sentences = abstract.split('.')
        contributions = []
        
        contribution_keywords = [
            'propose', 'introduce', 'present', 'develop',
            'achieve', 'improve', 'outperform', 'demonstrate'
        ]
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in contribution_keywords):
                contributions.append(sentence.strip())
        
        return contributions[:3]  # 最多3个主要贡献


class TrendAnalyzer:
    """趋势分析器"""
    
    def analyze_trends(self, papers: List[Dict]) -> Dict[str, Any]:
        """
        分析研究趋势
        
        Args:
            papers: 文献列表
        
        Returns:
            Dict: 趋势分析结果
        """
        if not papers:
            return {}
        
        return {
            'temporal_trend': self._analyze_temporal_trend(papers),
            'topic_evolution': self._analyze_topic_evolution(papers),
            'citation_trend': self._analyze_citation_trend(papers),
            'venue_distribution': self._analyze_venue_distribution(papers),
            'collaboration_network': self._analyze_collaboration(papers),
        }
    
    def _analyze_temporal_trend(self, papers: List[Dict]) -> Dict:
        """分析时间趋势"""
        year_counts = {}
        
        for paper in papers:
            year = paper.get('year', 0)
            if year > 0:
                year_counts[year] = year_counts.get(year, 0) + 1
        
        if not year_counts:
            return {}
        
        years = sorted(year_counts.keys())
        counts = [year_counts[y] for y in years]
        
        # 计算增长率
        growth_rate = 0.0
        if len(counts) > 1:
            growth_rate = (counts[-1] - counts[0]) / counts[0] * 100
        
        return {
            'years': years,
            'counts': counts,
            'growth_rate': round(growth_rate, 2),
            'peak_year': years[counts.index(max(counts))],
        }
    
    def _analyze_topic_evolution(self, papers: List[Dict]) -> Dict:
        """分析主题演化"""
        # 简化版：统计关键词频率
        keyword_freq = {}
        
        for paper in papers:
            abstract = paper.get('abstract', '').lower()
            words = abstract.split()
            
            for word in words:
                if len(word) > 4:  # 只统计长词
                    keyword_freq[word] = keyword_freq.get(word, 0) + 1
        
        # 取前20个高频词
        top_keywords = sorted(
            keyword_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]
        
        return {
            'top_keywords': [k for k, v in top_keywords],
            'frequencies': [v for k, v in top_keywords],
        }
    
    def _analyze_citation_trend(self, papers: List[Dict]) -> Dict:
        """分析引用趋势"""
        citations = [p.get('citationCount', 0) for p in papers]
        
        if not citations:
            return {}
        
        return {
            'total_citations': sum(citations),
            'average_citations': round(np.mean(citations), 2),
            'median_citations': int(np.median(citations)),
            'max_citations': max(citations),
            'highly_cited_count': sum(1 for c in citations if c > 100),
        }
    
    def _analyze_venue_distribution(self, papers: List[Dict]) -> Dict:
        """分析发表venue分布"""
        venue_counts = {}
        
        for paper in papers:
            venue = paper.get('venue', 'Unknown')
            if venue:
                venue_counts[venue] = venue_counts.get(venue, 0) + 1
        
        top_venues = sorted(
            venue_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'venues': [v for v, c in top_venues],
            'counts': [c for v, c in top_venues],
        }
    
    def _analyze_collaboration(self, papers: List[Dict]) -> Dict:
        """分析合作网络"""
        author_counts = {}
        
        for paper in papers:
            authors = paper.get('authors', [])
            for author in authors:
                if isinstance(author, dict):
                    name = author.get('name', '')
                else:
                    name = str(author)
                
                if name:
                    author_counts[name] = author_counts.get(name, 0) + 1
        
        top_authors = sorted(
            author_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]
        
        return {
            'top_authors': [a for a, c in top_authors],
            'paper_counts': [c for a, c in top_authors],
            'total_authors': len(author_counts),
        }


class AnalysisAgent:
    """
    分析智能体
    
    核心职责：
    1. 文献质量评分
    2. 关键信息提取
    3. 趋势分析
    4. 研究空白识别
    """
    
    def __init__(self):
        """初始化分析智能体"""
        self.scorer = PaperQualityScorer()
        self.extractor = KeyInformationExtractor()
        self.trend_analyzer = TrendAnalyzer()
        
        logger.info("分析智能体初始化完成")
    
    async def analyze_papers(
        self,
        papers: List[Dict],
        include_trends: bool = True,
    ) -> Dict[str, Any]:
        """
        分析文献集合
        
        Args:
            papers: 文献列表
            include_trends: 是否包含趋势分析
        
        Returns:
            Dict: 分析结果
        """
        logger.info(f"开始分析 {len(papers)} 篇文献")
        
        # 1. 质量评分
        scored_papers = []
        for paper in papers:
            score = self.scorer.score_paper(paper)
            paper['quality_score'] = score
            scored_papers.append(paper)
        
        # 按质量分数排序
        scored_papers.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # 2. 提取关键信息
        extracted_info = []
        for paper in scored_papers[:100]:  # 只处理前100篇
            info = self.extractor.extract(paper)
            info['quality_score'] = paper['quality_score']
            extracted_info.append(info)
        
        # 3. 趋势分析
        trends = {}
        if include_trends:
            trends = self.trend_analyzer.analyze_trends(scored_papers)
        
        # 4. 统计信息
        quality_scores = [p['quality_score'] for p in scored_papers]
        
        result = {
            'total_papers': len(papers),
            'analyzed_papers': len(scored_papers),
            'quality_statistics': {
                'average_score': round(np.mean(quality_scores), 2),
                'median_score': round(np.median(quality_scores), 2),
                'high_quality_count': sum(1 for s in quality_scores if s >= 80),
                'medium_quality_count': sum(1 for s in quality_scores if 60 <= s < 80),
                'low_quality_count': sum(1 for s in quality_scores if s < 60),
            },
            'top_papers': extracted_info[:20],
            'trends': trends,
            'timestamp': datetime.now().isoformat(),
        }
        
        logger.success(f"文献分析完成，平均质量分: {result['quality_statistics']['average_score']}")
        
        return result
    
    def filter_by_quality(
        self,
        papers: List[Dict],
        min_score: float = 60.0,
    ) -> List[Dict]:
        """
        按质量过滤文献
        
        Args:
            papers: 文献列表
            min_score: 最低质量分数
        
        Returns:
            List[Dict]: 过滤后的文献
        """
        filtered = []
        
        for paper in papers:
            if 'quality_score' not in paper:
                paper['quality_score'] = self.scorer.score_paper(paper)
            
            if paper['quality_score'] >= min_score:
                filtered.append(paper)
        
        logger.info(f"质量过滤：{len(papers)} -> {len(filtered)} 篇（阈值: {min_score}）")
        
        return filtered


# 创建全局分析智能体实例
analysis_agent = AnalysisAgent()