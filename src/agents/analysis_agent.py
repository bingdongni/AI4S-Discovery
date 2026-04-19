#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析智能体（Analysis Agent）
负责文献质量评分、关键信息提取、趋势分析
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
from collections import Counter
from loguru import logger
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class AnalysisAgent:
    """分析智能体"""
    
    def __init__(self):
        """初始化分析智能体"""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
        logger.info("分析智能体初始化完成")
    
    async def analyze_papers(
        self,
        papers: List[Dict],
        extract_keywords: bool = True,
        calculate_quality: bool = True,
        analyze_trends: bool = True,
    ) -> Dict:
        """
        分析文献集合
        
        Args:
            papers: 文献列表
            extract_keywords: 是否提取关键词
            calculate_quality: 是否计算质量分数
            analyze_trends: 是否分析趋势
        
        Returns:
            Dict: 分析结果
        """
        logger.info(f"开始分析 {len(papers)} 篇文献")
        
        results = {
            'total_papers': len(papers),
            'papers_with_scores': [],
            'keywords': [],
            'trends': {},
            'statistics': {},
        }
        
        if not papers:
            return results
        
        # 1. 质量评分
        if calculate_quality:
            scored_papers = []
            for paper in papers:
                score = self._calculate_quality_score(paper)
                paper_with_score = paper.copy()
                paper_with_score['quality_score'] = score
                scored_papers.append(paper_with_score)
            
            # 按质量分数排序
            scored_papers.sort(key=lambda x: x['quality_score'], reverse=True)
            results['papers_with_scores'] = scored_papers
            
            # 统计信息
            scores = [p['quality_score'] for p in scored_papers]
            results['statistics']['quality_scores'] = {
                'mean': np.mean(scores),
                'median': np.median(scores),
                'std': np.std(scores),
                'min': np.min(scores),
                'max': np.max(scores),
            }
            
            logger.info(f"质量评分完成，平均分: {results['statistics']['quality_scores']['mean']:.2f}")
        else:
            results['papers_with_scores'] = papers
        
        # 2. 关键词提取
        if extract_keywords:
            keywords = self._extract_keywords(papers)
            results['keywords'] = keywords
            logger.info(f"提取了 {len(keywords)} 个关键词")
        
        # 3. 趋势分析
        if analyze_trends:
            trends = self._analyze_trends(papers)
            results['trends'] = trends
            logger.info("趋势分析完成")
        
        # 4. 基础统计
        results['statistics'].update(self._calculate_statistics(papers))
        
        logger.success("文献分析完成")
        return results
    
    def _calculate_quality_score(self, paper: Dict) -> float:
        """
        计算文献质量分数（0-100）
        
        评分维度：
        1. 引用数（30分）
        2. 作者数量（10分）
        3. 摘要质量（20分）
        4. 发表年份（20分）
        5. 来源可信度（20分）
        
        Args:
            paper: 文献信息
        
        Returns:
            float: 质量分数
        """
        score = 0.0
        
        # 1. 引用数评分（30分）
        citation_count = paper.get('citationCount', 0)
        if citation_count > 0:
            # 对数缩放，100次引用得满分
            citation_score = min(30, 30 * np.log10(citation_count + 1) / np.log10(101))
            score += citation_score
        
        # 2. 作者数量评分（10分）
        authors = paper.get('authors', [])
        if authors:
            # 3-10个作者得满分
            author_score = min(10, len(authors) * 2)
            score += author_score
        
        # 3. 摘要质量评分（20分）
        abstract = paper.get('abstract', '')
        if abstract:
            # 基于长度和结构
            abstract_length = len(abstract)
            if abstract_length > 100:
                length_score = min(10, abstract_length / 200)
                score += length_score
            
            # 检查是否包含关键词
            keywords = ['method', 'result', 'conclusion', 'experiment', 'analysis', 'study']
            keyword_count = sum(1 for kw in keywords if kw in abstract.lower())
            keyword_score = min(10, keyword_count * 2)
            score += keyword_score
        
        # 4. 发表年份评分（20分）
        year = paper.get('year')
        if year:
            current_year = datetime.now().year
            years_ago = current_year - year
            if years_ago <= 2:
                year_score = 20  # 最近2年满分
            elif years_ago <= 5:
                year_score = 15  # 5年内15分
            elif years_ago <= 10:
                year_score = 10  # 10年内10分
            else:
                year_score = 5   # 10年以上5分
            score += year_score
        
        # 5. 来源可信度评分（20分）
        source = paper.get('source', '')
        source_scores = {
            'semantic_scholar': 20,
            'arxiv': 18,
            'pubmed': 20,
            'ieee': 20,
        }
        score += source_scores.get(source, 10)
        
        return round(score, 2)
    
    def _extract_keywords(self, papers: List[Dict], top_n: int = 50) -> List[Dict]:
        """
        从文献中提取关键词
        
        Args:
            papers: 文献列表
            top_n: 返回前N个关键词
        
        Returns:
            List[Dict]: 关键词列表，包含词频和TF-IDF分数
        """
        # 收集所有文本
        texts = []
        for paper in papers:
            text_parts = []
            if paper.get('title'):
                text_parts.append(paper['title'])
            if paper.get('abstract'):
                text_parts.append(paper['abstract'])
            texts.append(' '.join(text_parts))
        
        if not texts:
            return []
        
        try:
            # TF-IDF提取
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # 计算每个词的平均TF-IDF分数
            avg_tfidf = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # 获取top_n个关键词
            top_indices = avg_tfidf.argsort()[-top_n:][::-1]
            
            keywords = []
            for idx in top_indices:
                keyword = {
                    'term': feature_names[idx],
                    'tfidf_score': float(avg_tfidf[idx]),
                    'frequency': int(np.sum(tfidf_matrix[:, idx].toarray() > 0)),
                }
                keywords.append(keyword)
            
            return keywords
            
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []
    
    def _analyze_trends(self, papers: List[Dict]) -> Dict:
        """
        分析研究趋势
        
        Args:
            papers: 文献列表
        
        Returns:
            Dict: 趋势分析结果
        """
        trends = {
            'yearly_distribution': {},
            'author_distribution': {},
            'source_distribution': {},
            'citation_trends': {},
        }
        
        # 1. 年度分布
        years = [p.get('year') for p in papers if p.get('year')]
        if years:
            year_counts = Counter(years)
            trends['yearly_distribution'] = dict(sorted(year_counts.items()))
        
        # 2. 作者分布（高产作者）
        all_authors = []
        for paper in papers:
            authors = paper.get('authors', [])
            all_authors.extend(authors)
        
        if all_authors:
            author_counts = Counter(all_authors)
            top_authors = dict(author_counts.most_common(20))
            trends['author_distribution'] = top_authors
        
        # 3. 来源分布
        sources = [p.get('source') for p in papers if p.get('source')]
        if sources:
            source_counts = Counter(sources)
            trends['source_distribution'] = dict(source_counts)
        
        # 4. 引用趋势（按年份）
        citation_by_year = {}
        for paper in papers:
            year = paper.get('year')
            citations = paper.get('citationCount', 0)
            if year and citations:
                if year not in citation_by_year:
                    citation_by_year[year] = []
                citation_by_year[year].append(citations)
        
        # 计算每年的平均引用数
        for year, citations in citation_by_year.items():
            citation_by_year[year] = {
                'avg_citations': np.mean(citations),
                'total_citations': sum(citations),
                'paper_count': len(citations),
            }
        
        trends['citation_trends'] = dict(sorted(citation_by_year.items()))
        
        return trends
    
    def _calculate_statistics(self, papers: List[Dict]) -> Dict:
        """
        计算基础统计信息
        
        Args:
            papers: 文献列表
        
        Returns:
            Dict: 统计信息
        """
        stats = {
            'total_papers': len(papers),
            'papers_with_abstract': 0,
            'papers_with_citations': 0,
            'total_citations': 0,
            'avg_citations': 0,
            'year_range': {},
            'avg_authors_per_paper': 0,
        }
        
        if not papers:
            return stats
        
        # 统计摘要
        stats['papers_with_abstract'] = sum(1 for p in papers if p.get('abstract'))
        
        # 统计引用
        citations = [p.get('citationCount', 0) for p in papers]
        stats['papers_with_citations'] = sum(1 for c in citations if c > 0)
        stats['total_citations'] = sum(citations)
        stats['avg_citations'] = np.mean(citations) if citations else 0
        
        # 年份范围
        years = [p.get('year') for p in papers if p.get('year')]
        if years:
            stats['year_range'] = {
                'min': min(years),
                'max': max(years),
                'span': max(years) - min(years) + 1,
            }
        
        # 平均作者数
        author_counts = [len(p.get('authors', [])) for p in papers]
        stats['avg_authors_per_paper'] = np.mean(author_counts) if author_counts else 0
        
        return stats
    
    def filter_by_quality(
        self,
        papers: List[Dict],
        min_score: float = 40.0,
    ) -> List[Dict]:
        """
        根据质量分数过滤文献
        
        Args:
            papers: 文献列表（需要包含quality_score）
            min_score: 最低质量分数
        
        Returns:
            List[Dict]: 过滤后的文献列表
        """
        filtered = [p for p in papers if p.get('quality_score', 0) >= min_score]
        logger.info(f"质量过滤: {len(papers)} -> {len(filtered)} 篇（阈值: {min_score}）")
        return filtered
    
    def extract_key_findings(self, papers: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        提取关键发现（基于高质量文献的摘要）
        
        Args:
            papers: 文献列表
            top_n: 返回前N个关键发现
        
        Returns:
            List[Dict]: 关键发现列表
        """
        # 按质量分数排序
        sorted_papers = sorted(
            papers,
            key=lambda x: x.get('quality_score', 0),
            reverse=True
        )[:top_n]
        
        findings = []
        for paper in sorted_papers:
            finding = {
                'title': paper.get('title'),
                'authors': paper.get('authors', [])[:3],  # 前3位作者
                'year': paper.get('year'),
                'abstract': paper.get('abstract', '')[:300],  # 前300字符
                'quality_score': paper.get('quality_score'),
                'citations': paper.get('citationCount', 0),
                'source': paper.get('source'),
            }
            findings.append(finding)
        
        return findings


# 创建全局分析智能体实例
analysis_agent = AnalysisAgent()
