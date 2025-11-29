#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关联智能体（Relation Agent）
负责构建研究演进知识图谱，分析文献间的引用关系和主题关联
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
from datetime import datetime
from loguru import logger
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from src.core.config import settings


class RelationAgent:
    """关联智能体"""
    
    def __init__(self):
        """初始化关联智能体"""
        self.graph = nx.DiGraph()  # 有向图，表示引用关系
        self.similarity_threshold = 0.3  # 相似度阈值
        logger.info("关联智能体初始化完成")
    
    async def build_knowledge_graph(
        self,
        papers: List[Dict],
        include_citations: bool = True,
        include_similarity: bool = True,
        max_nodes: Optional[int] = None,
    ) -> Dict:
        """
        构建知识图谱
        
        Args:
            papers: 文献列表
            include_citations: 是否包含引用关系
            include_similarity: 是否包含相似度关系
            max_nodes: 最大节点数限制
        
        Returns:
            Dict: 图谱信息
        """
        logger.info(f"开始构建知识图谱，文献数: {len(papers)}")
        
        # 限制节点数
        if max_nodes and len(papers) > max_nodes:
            # 按质量分数排序，取前N个
            papers = sorted(
                papers,
                key=lambda x: x.get('quality_score', 0),
                reverse=True
            )[:max_nodes]
            logger.info(f"限制节点数为: {max_nodes}")
        
        # 清空现有图谱
        self.graph.clear()
        
        # 1. 添加节点
        self._add_nodes(papers)
        
        # 2. 添加引用关系边
        if include_citations:
            await self._add_citation_edges(papers)
        
        # 3. 添加相似度关系边
        if include_similarity:
            await self._add_similarity_edges(papers)
        
        # 4. 计算图谱统计信息
        stats = self._calculate_graph_statistics()
        
        # 5. 识别研究聚类
        clusters = self._identify_clusters()
        
        # 6. 识别关键节点
        key_nodes = self._identify_key_nodes()
        
        # 7. 分析研究演进路径
        evolution_paths = self._analyze_evolution_paths()
        
        result = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'statistics': stats,
            'clusters': clusters,
            'key_nodes': key_nodes,
            'evolution_paths': evolution_paths,
            'graph_data': self._export_graph_data(),
        }
        
        logger.success(f"知识图谱构建完成: {result['nodes']}节点, {result['edges']}边")
        return result
    
    def _add_nodes(self, papers: List[Dict]):
        """添加节点到图谱"""
        for paper in papers:
            paper_id = paper.get('paperId') or paper.get('title', '')
            
            # 节点属性
            node_attrs = {
                'title': paper.get('title', ''),
                'authors': paper.get('authors', []),
                'year': paper.get('year'),
                'abstract': paper.get('abstract', ''),
                'quality_score': paper.get('quality_score', 0),
                'citation_count': paper.get('citationCount', 0),
                'source': paper.get('source', ''),
                'keywords': paper.get('keywords', []),
            }
            
            self.graph.add_node(paper_id, **node_attrs)
        
        logger.info(f"添加了 {self.graph.number_of_nodes()} 个节点")
    
    async def _add_citation_edges(self, papers: List[Dict]):
        """添加引用关系边"""
        edge_count = 0
        
        # 构建paper_id到节点的映射
        paper_ids = set(self.graph.nodes())
        
        for paper in papers:
            paper_id = paper.get('paperId') or paper.get('title', '')
            
            # 获取引用列表（如果有）
            references = paper.get('references', [])
            citations = paper.get('citations', [])
            
            # 添加引用边（当前文献引用了其他文献）
            for ref in references:
                ref_id = ref if isinstance(ref, str) else ref.get('paperId')
                if ref_id and ref_id in paper_ids:
                    self.graph.add_edge(paper_id, ref_id, type='citation', weight=1.0)
                    edge_count += 1
            
            # 添加被引用边（其他文献引用了当前文献）
            for cit in citations:
                cit_id = cit if isinstance(cit, str) else cit.get('paperId')
                if cit_id and cit_id in paper_ids:
                    self.graph.add_edge(cit_id, paper_id, type='citation', weight=1.0)
                    edge_count += 1
        
        logger.info(f"添加了 {edge_count} 条引用关系边")
    
    async def _add_similarity_edges(self, papers: List[Dict]):
        """添加相似度关系边（基于文本相似度）"""
        if len(papers) < 2:
            return
        
        # 提取文本
        texts = []
        paper_ids = []
        
        for paper in papers:
            paper_id = paper.get('paperId') or paper.get('title', '')
            text_parts = []
            
            if paper.get('title'):
                text_parts.append(paper['title'])
            if paper.get('abstract'):
                text_parts.append(paper['abstract'])
            
            if text_parts:
                texts.append(' '.join(text_parts))
                paper_ids.append(paper_id)
        
        if len(texts) < 2:
            return
        
        try:
            # 计算TF-IDF相似度
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # 计算余弦相似度
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # 添加相似度边
            edge_count = 0
            for i in range(len(paper_ids)):
                for j in range(i + 1, len(paper_ids)):
                    similarity = similarity_matrix[i][j]
                    
                    # 只添加高相似度的边
                    if similarity >= self.similarity_threshold:
                        self.graph.add_edge(
                            paper_ids[i],
                            paper_ids[j],
                            type='similarity',
                            weight=float(similarity)
                        )
                        edge_count += 1
            
            logger.info(f"添加了 {edge_count} 条相似度关系边")
            
        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
    
    def _calculate_graph_statistics(self) -> Dict:
        """计算图谱统计信息"""
        stats = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'avg_degree': 0,
            'max_degree': 0,
            'connected_components': 0,
        }
        
        if self.graph.number_of_nodes() > 0:
            degrees = [d for n, d in self.graph.degree()]
            stats['avg_degree'] = np.mean(degrees)
            stats['max_degree'] = max(degrees)
            
            # 转换为无向图计算连通分量
            undirected = self.graph.to_undirected()
            stats['connected_components'] = nx.number_connected_components(undirected)
        
        return stats
    
    def _identify_clusters(self, max_clusters: int = 10) -> List[Dict]:
        """识别研究聚类（社区检测）"""
        if self.graph.number_of_nodes() < 2:
            return []
        
        try:
            # 转换为无向图
            undirected = self.graph.to_undirected()
            
            # 使用Louvain算法进行社区检测
            import community as community_louvain
            partition = community_louvain.best_partition(undirected)
            
            # 组织聚类信息
            clusters_dict = defaultdict(list)
            for node, cluster_id in partition.items():
                clusters_dict[cluster_id].append(node)
            
            # 构建聚类列表
            clusters = []
            for cluster_id, nodes in sorted(
                clusters_dict.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:max_clusters]:
                
                # 提取聚类主题（基于高频词）
                cluster_texts = []
                for node in nodes:
                    node_data = self.graph.nodes[node]
                    if node_data.get('title'):
                        cluster_texts.append(node_data['title'])
                
                cluster_info = {
                    'cluster_id': cluster_id,
                    'size': len(nodes),
                    'nodes': nodes[:10],  # 只返回前10个节点
                    'theme': self._extract_cluster_theme(cluster_texts),
                }
                clusters.append(cluster_info)
            
            logger.info(f"识别了 {len(clusters)} 个研究聚类")
            return clusters
            
        except ImportError:
            logger.warning("未安装python-louvain，使用简单聚类")
            return self._simple_clustering(max_clusters)
        except Exception as e:
            logger.error(f"聚类识别失败: {e}")
            return []
    
    def _simple_clustering(self, max_clusters: int = 10) -> List[Dict]:
        """简单聚类（基于连通分量）"""
        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))
        
        clusters = []
        for idx, component in enumerate(sorted(components, key=len, reverse=True)[:max_clusters]):
            nodes = list(component)
            cluster_texts = [
                self.graph.nodes[n].get('title', '')
                for n in nodes
                if self.graph.nodes[n].get('title')
            ]
            
            clusters.append({
                'cluster_id': idx,
                'size': len(nodes),
                'nodes': nodes[:10],
                'theme': self._extract_cluster_theme(cluster_texts),
            })
        
        return clusters
    
    def _extract_cluster_theme(self, texts: List[str]) -> str:
        """提取聚类主题"""
        if not texts:
            return "未知主题"
        
        try:
            # 使用TF-IDF提取关键词
            vectorizer = TfidfVectorizer(max_features=5, stop_words='english')
            vectorizer.fit_transform(texts)
            keywords = vectorizer.get_feature_names_out()
            return ', '.join(keywords)
        except:
            return "未知主题"
    
    def _identify_key_nodes(self, top_n: int = 10) -> List[Dict]:
        """识别关键节点（基于多种中心性指标）"""
        if self.graph.number_of_nodes() == 0:
            return []
        
        key_nodes = []
        
        try:
            # 1. 度中心性（连接数）
            degree_centrality = nx.degree_centrality(self.graph)
            
            # 2. 介数中心性（桥接作用）
            betweenness_centrality = nx.betweenness_centrality(self.graph)
            
            # 3. PageRank（重要性）
            pagerank = nx.pagerank(self.graph)
            
            # 综合评分
            node_scores = {}
            for node in self.graph.nodes():
                score = (
                    degree_centrality.get(node, 0) * 0.3 +
                    betweenness_centrality.get(node, 0) * 0.3 +
                    pagerank.get(node, 0) * 0.4
                )
                node_scores[node] = score
            
            # 排序并返回top N
            sorted_nodes = sorted(
                node_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n]
            
            for node, score in sorted_nodes:
                node_data = self.graph.nodes[node]
                key_nodes.append({
                    'node_id': node,
                    'title': node_data.get('title', ''),
                    'year': node_data.get('year'),
                    'importance_score': round(score, 4),
                    'degree': self.graph.degree(node),
                    'citation_count': node_data.get('citation_count', 0),
                })
            
            logger.info(f"识别了 {len(key_nodes)} 个关键节点")
            
        except Exception as e:
            logger.error(f"关键节点识别失败: {e}")
        
        return key_nodes
    
    def _analyze_evolution_paths(self, max_paths: int = 5) -> List[Dict]:
        """分析研究演进路径"""
        if self.graph.number_of_nodes() < 2:
            return []
        
        paths = []
        
        try:
            # 按年份排序节点
            nodes_by_year = defaultdict(list)
            for node in self.graph.nodes():
                year = self.graph.nodes[node].get('year')
                if year:
                    nodes_by_year[year].append(node)
            
            if len(nodes_by_year) < 2:
                return []
            
            # 找到最早和最晚的年份
            years = sorted(nodes_by_year.keys())
            early_nodes = nodes_by_year[years[0]]
            recent_nodes = nodes_by_year[years[-1]]
            
            # 寻找从早期到近期的路径
            path_count = 0
            for start_node in early_nodes[:3]:  # 限制起点数量
                for end_node in recent_nodes[:3]:  # 限制终点数量
                    try:
                        # 寻找最短路径
                        path = nx.shortest_path(self.graph, start_node, end_node)
                        
                        if len(path) > 1:
                            path_info = {
                                'length': len(path),
                                'start_year': years[0],
                                'end_year': years[-1],
                                'nodes': [
                                    {
                                        'title': self.graph.nodes[n].get('title', ''),
                                        'year': self.graph.nodes[n].get('year'),
                                    }
                                    for n in path
                                ],
                            }
                            paths.append(path_info)
                            path_count += 1
                            
                            if path_count >= max_paths:
                                break
                    except nx.NetworkXNoPath:
                        continue
                
                if path_count >= max_paths:
                    break
            
            logger.info(f"分析了 {len(paths)} 条研究演进路径")
            
        except Exception as e:
            logger.error(f"演进路径分析失败: {e}")
        
        return paths
    
    def _export_graph_data(self) -> Dict:
        """导出图谱数据（用于可视化）"""
        nodes_data = []
        edges_data = []
        
        # 导出节点
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            nodes_data.append({
                'id': node,
                'label': node_data.get('title', '')[:50],  # 限制长度
                'year': node_data.get('year'),
                'quality_score': node_data.get('quality_score', 0),
                'citation_count': node_data.get('citation_count', 0),
            })
        
        # 导出边
        for source, target, data in self.graph.edges(data=True):
            edges_data.append({
                'source': source,
                'target': target,
                'type': data.get('type', 'unknown'),
                'weight': data.get('weight', 1.0),
            })
        
        return {
            'nodes': nodes_data,
            'edges': edges_data,
        }
    
    def get_node_neighbors(self, node_id: str, max_neighbors: int = 10) -> List[Dict]:
        """获取节点的邻居"""
        if node_id not in self.graph:
            return []
        
        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            neighbor_data = self.graph.nodes[neighbor]
            edge_data = self.graph[node_id][neighbor]
            
            neighbors.append({
                'node_id': neighbor,
                'title': neighbor_data.get('title', ''),
                'year': neighbor_data.get('year'),
                'relation_type': edge_data.get('type', 'unknown'),
                'weight': edge_data.get('weight', 1.0),
            })
        
        # 按权重排序
        neighbors.sort(key=lambda x: x['weight'], reverse=True)
        return neighbors[:max_neighbors]


# 创建全局关联智能体实例
relation_agent = RelationAgent()
