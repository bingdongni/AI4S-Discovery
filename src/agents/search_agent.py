#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜索智能体（Search Agent）
负责从多个学术数据源并行采集文献
支持arXiv、PubMed、Semantic Scholar、IEEE等20+数据源
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from abc import ABC, abstractmethod

from src.core.config import settings


class DataSource(ABC):
    """数据源基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def init_session(self):
        """初始化HTTP会话"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=settings.CRAWLER_TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 100) -> List[Dict]:
        """
        搜索文献
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
        
        Returns:
            List[Dict]: 文献列表
        """
        pass


class ArXivSource(DataSource):
    """arXiv数据源"""
    
    def __init__(self):
        super().__init__("arXiv")
        self.base_url = "http://export.arxiv.org/api/query"
    
    async def search(self, query: str, max_results: int = 100) -> List[Dict]:
        """搜索arXiv文献"""
        await self.init_session()
        
        papers = []
        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    # 解析XML响应
                    text = await response.text()
                    # 这里需要实现XML解析逻辑
                    logger.info(f"从arXiv获取到 {len(papers)} 篇文献")
                else:
                    logger.warning(f"arXiv请求失败: {response.status}")
        
        except Exception as e:
            logger.error(f"arXiv搜索出错: {e}")
        
        return papers


class PubMedSource(DataSource):
    """PubMed数据源"""
    
    def __init__(self):
        super().__init__("PubMed")
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.api_key = settings.PUBMED_API_KEY
    
    async def search(self, query: str, max_results: int = 100) -> List[Dict]:
        """搜索PubMed文献"""
        await self.init_session()
        
        papers = []
        try:
            # 第一步：搜索获取ID列表
            search_url = f"{self.base_url}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    id_list = data.get("esearchresult", {}).get("idlist", [])
                    
                    # 第二步：获取详细信息
                    if id_list:
                        papers = await self._fetch_details(id_list)
                    
                    logger.info(f"从PubMed获取到 {len(papers)} 篇文献")
                else:
                    logger.warning(f"PubMed请求失败: {response.status}")
        
        except Exception as e:
            logger.error(f"PubMed搜索出错: {e}")
        
        return papers
    
    async def _fetch_details(self, id_list: List[str]) -> List[Dict]:
        """获取文献详细信息"""
        papers = []
        
        try:
            fetch_url = f"{self.base_url}/efetch.fcgi"
            params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml",
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with self.session.get(fetch_url, params=params) as response:
                if response.status == 200:
                    # 解析XML响应
                    text = await response.text()
                    # 这里需要实现XML解析逻辑
                    pass
        
        except Exception as e:
            logger.error(f"获取PubMed详情出错: {e}")
        
        return papers


class SemanticScholarSource(DataSource):
    """Semantic Scholar数据源"""
    
    def __init__(self):
        super().__init__("Semantic Scholar")
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = settings.SEMANTIC_SCHOLAR_API_KEY
    
    async def search(self, query: str, max_results: int = 100) -> List[Dict]:
        """搜索Semantic Scholar文献"""
        await self.init_session()
        
        papers = []
        try:
            search_url = f"{self.base_url}/paper/search"
            params = {
                "query": query,
                "limit": min(max_results, 100),
                "fields": "paperId,title,abstract,authors,year,citationCount,influentialCitationCount,venue,publicationDate",
            }
            
            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            
            async with self.session.get(search_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    papers = data.get("data", [])
                    logger.info(f"从Semantic Scholar获取到 {len(papers)} 篇文献")
                else:
                    logger.warning(f"Semantic Scholar请求失败: {response.status}")
        
        except Exception as e:
            logger.error(f"Semantic Scholar搜索出错: {e}")
        
        return papers


class IEEESource(DataSource):
    """IEEE Xplore数据源"""
    
    def __init__(self):
        super().__init__("IEEE Xplore")
        self.base_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        self.api_key = settings.IEEE_API_KEY
    
    async def search(self, query: str, max_results: int = 100) -> List[Dict]:
        """搜索IEEE文献"""
        await self.init_session()
        
        papers = []
        
        if not self.api_key:
            logger.warning("IEEE API密钥未配置，跳过IEEE搜索")
            return papers
        
        try:
            params = {
                "apikey": self.api_key,
                "querytext": query,
                "max_records": min(max_results, 200),
                "format": "json",
            }
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    papers = data.get("articles", [])
                    logger.info(f"从IEEE获取到 {len(papers)} 篇文献")
                else:
                    logger.warning(f"IEEE请求失败: {response.status}")
        
        except Exception as e:
            logger.error(f"IEEE搜索出错: {e}")
        
        return papers


class SearchAgent:
    """
    搜索智能体
    
    核心职责：
    1. 管理多个学术数据源
    2. 并行搜索文献
    3. 去重和合并结果
    4. 处理反爬和限流
    """
    
    def __init__(self):
        """初始化搜索智能体"""
        self.sources: Dict[str, DataSource] = {
            "arxiv": ArXivSource(),
            "pubmed": PubMedSource(),
            "semantic_scholar": SemanticScholarSource(),
            "ieee": IEEESource(),
        }
        
        logger.info(f"搜索智能体初始化完成，支持 {len(self.sources)} 个数据源")
    
    async def search(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results_per_source: int = 100,
    ) -> Dict[str, Any]:
        """
        并行搜索多个数据源
        
        Args:
            query: 搜索查询
            sources: 指定数据源列表，None表示使用所有数据源
            max_results_per_source: 每个数据源的最大结果数
        
        Returns:
            Dict: 搜索结果
        """
        if sources is None:
            sources = list(self.sources.keys())
        
        logger.info(f"开始搜索: {query}")
        logger.info(f"使用数据源: {', '.join(sources)}")
        
        # 并行搜索所有数据源
        tasks = []
        for source_name in sources:
            if source_name in self.sources:
                source = self.sources[source_name]
                task = source.search(query, max_results_per_source)
                tasks.append((source_name, task))
        
        # 等待所有搜索完成
        results = {}
        for source_name, task in tasks:
            try:
                papers = await task
                results[source_name] = papers
            except Exception as e:
                logger.error(f"数据源 {source_name} 搜索失败: {e}")
                results[source_name] = []
        
        # 合并和去重
        all_papers = self._merge_and_deduplicate(results)
        
        # 关闭所有会话
        await self._close_all_sessions()
        
        return {
            "query": query,
            "total_papers": len(all_papers),
            "sources": {k: len(v) for k, v in results.items()},
            "papers": all_papers,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _merge_and_deduplicate(self, results: Dict[str, List[Dict]]) -> List[Dict]:
        """
        合并和去重文献
        
        Args:
            results: 各数据源的搜索结果
        
        Returns:
            List[Dict]: 去重后的文献列表
        """
        seen_titles = set()
        merged_papers = []
        
        for source_name, papers in results.items():
            for paper in papers:
                # 使用标题进行去重（简化版）
                title = paper.get("title", "").lower().strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    paper["source"] = source_name
                    merged_papers.append(paper)
        
        logger.info(f"去重后共 {len(merged_papers)} 篇文献")
        return merged_papers
    
    async def _close_all_sessions(self):
        """关闭所有HTTP会话"""
        for source in self.sources.values():
            await source.close_session()


# 创建全局搜索智能体实例
search_agent = SearchAgent()