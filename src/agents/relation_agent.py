#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关联智能体（Relation Agent）
负责构建研究演进图谱和知识关联分析
"""

import networkx as nx
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from loguru import logger
from collections import defaultdict

from src.core.config import settings


class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self):
        """初始化图谱构建器"""
        self.graph = nx.DiGraph()
        self.node_types = {
            'paper': 0,
            'author': 0,
            'concept': 0,
            'method': 0,
            'dataset': 0,
        }
    
    def build_graph(self, papers: List[Dict]) -> nx.DiGraph:
        """
        构建知识图谱
        
        Args:
            papers: 文献列表
        
        Returns:
            nx.DiGraph: 知识图谱
        """
        logger.info(f"开始构建知识图谱，文献数: {len(papers)}")
        
        # 添加文献节点
        for paper in papers:
            self._add_paper_node(paper)
        
        # 添加作者节点和关系
        for paper in papers:
            self._add_author_relations(paper)
        
        # 添加引用关系
        self._add_citation_relations(papers)
        
        # 添加概念节点和关系
        for paper in papers:
            self._add_concept_relations(paper)
        
        logger.success(f"图谱构建完成: {self.graph.number_of_nodes()} 节点, {self.graph.number_of_edges()} 边")
        
        return self.graph
    
    def _add_paper_node(self, paper: Dict):
        """添加文献节点"""
        paper_id = paper.get('paperId') or paper.get('title', '')[:50]
        
        self.graph.add_node(
            paper_id,
            type='paper',
            title=paper.get('title', ''),
            year=paper.get('year', 0),
            citations=paper.get('citationCount', 0),
            quality_score=paper.get('quality_score', 0),
        )
        
        self.node_types['paper'] += 1
    
    def _add_author_relations(self, paper: Dict):
        """添加作者关系"""
        paper_id = paper.get('paperId') or paper.get('title', '')[:50]
        authors = paper.get('authors', [])
        
        for author in authors:
            if isinstance(author, dict):
                author_name = author.get('name', '')
            else:
                author_name = str(author)
            
            if not author_name:
                continue
            
            # 添加作者节点
            if not self.graph.has_node(author_name):
                self.graph.add_node(
                    author_name,
                    type='author',
                    papers=[]
                )
                self.node_types['author'] += 1
            
            # 添加作者-文献关系
            self.graph.add_edge(author_name, paper_id, relation='authored')
            
            # 更新作者的文献列表
            if 'papers' in self.graph.nodes[author_name]:
                self.graph.nodes[author_name]['papers'].append(paper_id)
    
    def _add_citation_relations(self, papers: List[Dict]):
        """添加引用关系"""
        # 简化版：基于时间顺序推断引用关系
        papers_by_year = defaultdict(list)
        
        for paper in papers:
            year = paper.get('year', 0)
            if year > 0:
                paper_id = paper.get('paperId') or paper.get('title', '')[:50]
                papers_by_year[year].append(paper_id)
        
        # 假设新文献引用旧文献
        years = sorted(papers_by_year.keys())
        for i, year in enumerate(years):
            if i > 0:
                # 当前年份的文献可能引用前一年的文献
                current_papers = papers_by_year[year]
                previous_papers = papers_by_year[years[i-1]]
                
                for curr_paper in current_papers[:5]:  # 限制数量
                    for prev_paper in previous_papers[:3]:
                        if self.graph.has_node(curr_paper) and self.graph.has_node(prev_paper):
                            self.graph.add_edge(curr_paper, prev_paper, relation='cites')
    
    def _add_concept_relations(self, paper: Dict):
        """添加概念关系"""
        paper_id = paper.get('paperId') or paper.get('title', '')[:50]
        
        # 从摘要中提取概念
        abstract = paper.get('abstract', '').lower()
        
        # 预定义的概念关键词
        concepts = {
            'deep learning': ['deep learning', 'neural network', 'cnn', 'rnn'],
            'machine learning': ['machine learning', 'supervised', 'unsupervised'],
            'natural language processing': ['nlp', 'language model', 'transformer'],
            'computer vision': ['computer vision', 'image', 'object detection'],
            'reinforcement learning': ['reinforcement learning', 'policy', 'reward'],
        }
        
        for concept_name, keywords in concepts.items():
            if any(kw in abstract for kw in keywords):
                # 添加概念节点
                if not self.graph.has_node(concept_name):
                    self.graph.add_node(
                        concept_name,
                        type='concept',
                        papers=[]
                    )
                    self.node_types['concept'] += 1
                
                # 添加文献-概念关系
                self.graph.add_edge(paper_id, concept_name, relation='about')
                
                if 'papers' in self.graph.nodes[concept_name]:
                    self.graph.nodes[concept_name]['papers'].append(paper_id)
    
    def get_statistics(self) -> Dict:
        """获取图谱统计信息"""
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': self.node_types.copy(),
            'density': nx.density(self.graph),
            'is_connected': nx.is_weakly_connected(self.graph),
        }
    
    def find_central_papers(self, top_k: int = 10) -> List[Tuple[str, float]]:
        """查找中心文献（基于PageRank）"""
        if self.graph.number_of_nodes() == 0:
            return []
        
        try:
            pagerank = nx.pagerank(self.graph)
            
            # 只返回文献节点
            paper_ranks = [
                (node, rank)
                for node, rank in pagerank.items()
                if self.graph.nodes[node].get('type') == 'paper'
            ]
            
            paper_ranks.sort(key=lambda x: x[1], reverse=True)
            return paper_ranks[:top_k]
        except:
            return []
    
    def find_communities(self) -> List[List[str]]:
        """发现研究社区"""
        if self.graph.number_of_nodes() == 0:
            return []
        
        try:
            # 转换为无向图进行社区发现
            undirected = self.graph.to_undirected()
            communities = list(nx.community.greedy_modularity_communities(undirected))
            return [list(community) for community in communities]
        except:
            return []


class ResearchEvolutionAnalyzer:
    """研究演进分析器"""
    
    def analyze_evolution(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """
        分析研究演进
        
        Args:
            graph: 知识图谱
        
        Returns:
            Dict: 演进分析结果
        """
        return {
            'temporal_evolution': self._analyze_temporal_evolution(graph),
            'concept_evolution': self._analyze_concept_evolution(graph),
            'collaboration_evolution': self._analyze_collaboration_evolution(graph),
            'impact_evolution': self._analyze_impact_evolution(graph),
        }
    
    def _analyze_temporal_evolution(self, graph: nx.DiGraph) -> Dict:
        """分析时间演进"""
        papers_by_year = defaultdict(int)
        
        for node, data in graph.nodes(data=True):
            if data.get('type') == 'paper':
                year = data.get('year', 0)
                if year > 0:
                    papers_by_year[year] += 1
        
        years = sorted(papers_by_year.keys())
        counts = [papers_by_year[y] for y in years]
        
        return {
            'years': years,
            'paper_counts': counts,
            'total_years': len(years),
            'growth_trend': 'increasing' if len(counts) > 1 and counts[-1] > counts[0] else 'stable',
        }
    
    def _analyze_concept_evolution(self, graph: nx.DiGraph) -> Dict:
        """分析概念演进"""
        concept_papers = defaultdict(list)
        
        for node, data in graph.nodes(data=True):
            if data.get('type') == 'concept':
                papers = data.get('papers', [])
                concept_papers[node] = len(papers)
        
        top_concepts = sorted(
            concept_papers.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'top_concepts': [c for c, count in top_concepts],
            'paper_counts': [count for c, count in top_concepts],
        }
    
    def _analyze_collaboration_evolution(self, graph: nx.DiGraph) -> Dict:
        """分析合作演进"""
        author_papers = defaultdict(int)
        
        for node, data in graph.nodes(data=True):
            if data.get('type') == 'author':
                papers = data.get('papers', [])
                author_papers[node] = len(papers)
        
        top_authors = sorted(
            author_papers.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'top_authors': [a for a, count in top_authors],
            'paper_counts': [count for a, count in top_authors],
            'total_authors': len(author_papers),
        }
    
    def _analyze_impact_evolution(self, graph: nx.DiGraph) -> Dict:
        """分析影响力演进"""
        high_impact_papers = []
        
        for node, data in graph.nodes(data=True):
            if data.get('type') == 'paper':
                citations = data.get('citations', 0)
                if citations > 50:  # 高影响力阈值
                    high_impact_papers.append({
                        'title': data.get('title', ''),
                        'year': data.get('year', 0),
                        'citations': citations,
                    })
        
        high_impact_papers.sort(key=lambda x: x['citations'], reverse=True)
        
        return {
            'high_impact_count': len(high_impact_papers),
            'top_papers': high_impact_papers[:10],
        }


class RelationAgent:
    """
    关联智能体
    
    核心职责：
    1. 构建知识图谱
    2. 分析研究演进
    3. 发现研究社区
    4. 识别研究空白
    """
    
    def __init__(self):
        """初始化关联智能体"""
        self.graph_builder = KnowledgeGraphBuilder()
        self.evolution_analyzer = ResearchEvolutionAnalyzer()
        
        logger.info("关联智能体初始化完成")
    
    async def build_knowledge_graph(
        self,
        papers: List[Dict],
    ) -> Dict[str, Any]:
        """
        构建知识图谱
        
        Args:
            papers: 文献列表
        
        Returns:
            Dict: 图谱构建结果
        """
        logger.info(f"开始构建知识图谱")
        
        # 构建图谱
        graph = self.graph_builder.build_graph(papers)
        
        # 获取统计信息
        statistics = self.graph_builder.get_statistics()
        
        # 查找中心文献
        central_papers = self.graph_builder.find_central_papers(top_k=10)
        
        # 发现研究社区
        communities = self.graph_builder.find_communities()
        
        # 分析演进
        evolution = self.evolution_analyzer.analyze_evolution(graph)
        
        result = {
            'statistics': statistics,
            'central_papers': [
                {'paper_id': paper_id, 'importance': float(score)}
                for paper_id, score in central_papers
            ],
            'communities': [
                {'id': i, 'size': len(comm), 'members': comm[:10]}
                for i, comm in enumerate(communities[:5])
            ],
            'evolution': evolution,
            'timestamp': datetime.now().isoformat(),
        }
        
        logger.success(f"知识图谱构建完成")
        
        return result
    
    def identify_research_gaps(
        self,
        graph: nx.DiGraph,
        papers: List[Dict],
    ) -> List[Dict]:
        """
        识别研究空白
        
        Args:
            graph: 知识图谱
            papers: 文献列表
        
        Returns:
            List[Dict]: 研究空白列表
        """
        gaps = []
        
        # 1. 低连接度的概念（研究不足）
        for node, data in graph.nodes(data=True):
            if data.get('type') == 'concept':
                degree = graph.degree(node)
                if degree < 5:  # 低连接度阈值
                    gaps.append({
                        'type': 'under_researched_concept',
                        'concept': node,
                        'paper_count': len(data.get('papers', [])),
                        'priority': 'high',
                    })
        
        # 2. 缺失的跨域连接
        concepts = [n for n, d in graph.nodes(data=True) if d.get('type') == 'concept']
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                # 检查两个概念之间是否有共同的文献
                papers1 = set(graph.nodes[concept1].get('papers', []))
                papers2 = set(graph.nodes[concept2].get('papers', []))
                common = papers1 & papers2
                
                if len(common) == 0:
                    gaps.append({
                        'type': 'missing_cross_domain',
                        'concepts': [concept1, concept2],
                        'priority': 'medium',
                    })
        
        logger.info(f"识别到 {len(gaps)} 个研究空白")
        
        return gaps[:20]  # 返回前20个


# 创建全局关联智能体实例
relation_agent = RelationAgent()