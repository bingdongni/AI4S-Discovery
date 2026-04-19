#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向量数据库管理器
用于语义搜索和相似文献推荐
支持FAISS本地向量存储
"""

import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
import faiss
from sentence_transformers import SentenceTransformer

from src.core.config import settings


class VectorStore:
    """向量数据库管理器"""
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        index_path: Optional[str] = None,
        dimension: int = 384
    ):
        """
        初始化向量存储
        
        Args:
            model_name: 句子编码模型名称
            index_path: 索引文件路径
            dimension: 向量维度
        """
        self.model_name = model_name
        self.dimension = dimension
        self.index_path = index_path or str(Path(settings.DATA_DIR) / "vector_index.faiss")
        self.metadata_path = str(Path(settings.DATA_DIR) / "vector_metadata.pkl")
        
        # 初始化编码模型
        logger.info(f"加载句子编码模型: {model_name}")
        self.encoder = SentenceTransformer(model_name)
        
        # 初始化FAISS索引
        self.index = None
        self.metadata = []
        
        # 尝试加载已有索引
        self._load_index()
        
        if self.index is None:
            self._create_index()
        
        logger.info(f"向量数据库初始化完成，当前向量数: {self.index.ntotal}")
    
    def _create_index(self):
        """创建新的FAISS索引"""
        # 使用IndexFlatL2进行精确搜索（适合中小规模数据）
        # 对于大规模数据，可以使用IndexIVFFlat或IndexHNSW
        self.index = faiss.IndexFlatL2(self.dimension)
        logger.info(f"创建新的FAISS索引，维度: {self.dimension}")
    
    def _load_index(self):
        """加载已有的索引"""
        try:
            if Path(self.index_path).exists():
                self.index = faiss.read_index(self.index_path)
                logger.info(f"加载FAISS索引: {self.index_path}")
                
                if Path(self.metadata_path).exists():
                    with open(self.metadata_path, 'rb') as f:
                        self.metadata = pickle.load(f)
                    logger.info(f"加载元数据: {len(self.metadata)}条")
        except Exception as e:
            logger.warning(f"加载索引失败: {e}")
            self.index = None
            self.metadata = []
    
    def save_index(self):
        """保存索引到磁盘"""
        try:
            # 确保目录存在
            Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存FAISS索引
            faiss.write_index(self.index, self.index_path)
            
            # 保存元数据
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            logger.info(f"索引已保存: {self.index_path}")
        except Exception as e:
            logger.error(f"保存索引失败: {e}")
    
    def encode_text(self, texts: List[str]) -> np.ndarray:
        """
        将文本编码为向量
        
        Args:
            texts: 文本列表
        
        Returns:
            向量数组
        """
        embeddings = self.encoder.encode(texts, show_progress_bar=False)
        return np.array(embeddings).astype('float32')
    
    def add_papers(self, papers: List[Dict[str, Any]]):
        """
        添加文献到向量数据库
        
        Args:
            papers: 文献列表
        """
        if not papers:
            return
        
        logger.info(f"添加{len(papers)}篇文献到向量数据库")
        
        # 准备文本（标题+摘要）
        texts = []
        valid_papers = []
        
        for paper in papers:
            title = paper.get('title', '')
            abstract = paper.get('abstract', '')
            
            if title or abstract:
                text = f"{title}. {abstract}"
                texts.append(text)
                valid_papers.append(paper)
        
        if not texts:
            logger.warning("没有有效的文本可以编码")
            return
        
        # 编码文本
        embeddings = self.encode_text(texts)
        
        # 添加到索引
        self.index.add(embeddings)
        
        # 保存元数据
        for paper in valid_papers:
            self.metadata.append({
                'paper_id': paper.get('paperId') or paper.get('id'),
                'title': paper.get('title'),
                'authors': paper.get('authors', []),
                'year': paper.get('year'),
                'abstract': paper.get('abstract', '')[:200],  # 只保存前200字符
                'citationCount': paper.get('citationCount', 0),
            })
        
        logger.success(f"成功添加{len(valid_papers)}篇文献，当前总数: {self.index.ntotal}")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        语义搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值
        
        Returns:
            相似文献列表
        """
        if self.index.ntotal == 0:
            logger.warning("向量数据库为空")
            return []
        
        # 编码查询
        query_vector = self.encode_text([query])
        
        # 搜索
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        # 转换距离为相似度（L2距离转余弦相似度的近似）
        # 相似度 = 1 / (1 + distance)
        similarities = 1 / (1 + distances[0])
        
        # 构建结果
        results = []
        for idx, similarity in zip(indices[0], similarities):
            if idx < len(self.metadata) and similarity >= min_similarity:
                result = self.metadata[idx].copy()
                result['similarity'] = float(similarity)
                results.append(result)
        
        logger.info(f"语义搜索完成，找到{len(results)}个结果")
        return results
    
    def find_similar_papers(
        self,
        paper_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查找相似文献
        
        Args:
            paper_id: 文献ID
            top_k: 返回结果数量
        
        Returns:
            相似文献列表
        """
        # 查找文献在元数据中的索引
        paper_idx = None
        for idx, meta in enumerate(self.metadata):
            if meta.get('paper_id') == paper_id:
                paper_idx = idx
                break
        
        if paper_idx is None:
            logger.warning(f"未找到文献: {paper_id}")
            return []
        
        # 获取文献向量
        paper_vector = self.index.reconstruct(paper_idx).reshape(1, -1)
        
        # 搜索相似向量（排除自身）
        distances, indices = self.index.search(paper_vector, top_k + 1)
        
        # 构建结果（排除第一个，即自身）
        results = []
        for idx, distance in zip(indices[0][1:], distances[0][1:]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result['similarity'] = float(1 / (1 + distance))
                results.append(result)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'model_name': self.model_name,
            'index_type': type(self.index).__name__,
        }
    
    def clear(self):
        """清空索引"""
        self._create_index()
        self.metadata = []
        logger.info("向量数据库已清空")
    
    def batch_search(
        self,
        queries: List[str],
        top_k: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """
        批量语义搜索
        
        Args:
            queries: 查询文本列表
            top_k: 每个查询返回的结果数量
        
        Returns:
            每个查询的结果列表
        """
        if self.index.ntotal == 0:
            return [[] for _ in queries]
        
        # 批量编码
        query_vectors = self.encode_text(queries)
        
        # 批量搜索
        distances, indices = self.index.search(query_vectors, min(top_k, self.index.ntotal))
        
        # 构建结果
        all_results = []
        for query_distances, query_indices in zip(distances, indices):
            similarities = 1 / (1 + query_distances)
            
            results = []
            for idx, similarity in zip(query_indices, similarities):
                if idx < len(self.metadata):
                    result = self.metadata[idx].copy()
                    result['similarity'] = float(similarity)
                    results.append(result)
            
            all_results.append(results)
        
        return all_results
    
    def update_paper(self, paper_id: str, paper: Dict[str, Any]):
        """
        更新文献信息
        
        Args:
            paper_id: 文献ID
            paper: 新的文献信息
        """
        # 查找并更新元数据
        for idx, meta in enumerate(self.metadata):
            if meta.get('paper_id') == paper_id:
                # 更新元数据
                self.metadata[idx] = {
                    'paper_id': paper.get('paperId') or paper.get('id'),
                    'title': paper.get('title'),
                    'authors': paper.get('authors', []),
                    'year': paper.get('year'),
                    'abstract': paper.get('abstract', '')[:200],
                    'citationCount': paper.get('citationCount', 0),
                }
                
                # 重新编码并更新向量
                text = f"{paper.get('title', '')}. {paper.get('abstract', '')}"
                embedding = self.encode_text([text])
                
                # FAISS不支持直接更新，需要重建索引
                # 这里简化处理，只更新元数据
                logger.info(f"更新文献元数据: {paper_id}")
                break
    
    def remove_paper(self, paper_id: str):
        """
        删除文献
        
        Args:
            paper_id: 文献ID
        """
        # FAISS不支持直接删除，需要重建索引
        # 这里标记为删除，实际删除需要重建索引
        for meta in self.metadata:
            if meta.get('paper_id') == paper_id:
                meta['deleted'] = True
                logger.info(f"标记文献为删除: {paper_id}")
                break
    
    def rebuild_index(self):
        """重建索引（移除已删除的文献）"""
        # 过滤未删除的文献
        valid_metadata = [m for m in self.metadata if not m.get('deleted', False)]
        
        if not valid_metadata:
            self.clear()
            return
        
        # 重新编码所有文献
        texts = [f"{m['title']}. {m.get('abstract', '')}" for m in valid_metadata]
        embeddings = self.encode_text(texts)
        
        # 创建新索引
        self._create_index()
        self.index.add(embeddings)
        self.metadata = valid_metadata
        
        logger.info(f"索引重建完成，当前向量数: {self.index.ntotal}")


# 创建全局向量存储实例
vector_store = VectorStore()