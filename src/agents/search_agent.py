#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜索智能体（Search Agent）
负责从多个学术数据源并行采集文献
支持arXiv、PubMed、Semantic Scholar、IEEE等数据源
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime
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

    def _parse_arxiv_xml(self, xml_text: str) -> List[Dict]:
        """
        解析arXiv XML响应

        Args:
            xml_text: XML响应文本

        Returns:
            List[Dict]: 解析后的文献列表
        """
        papers = []

        try:
            # 移除命名空间以便更简单地解析
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}

            root = ET.fromstring(xml_text)

            # 处理带命名空间和不带命名空间两种情况
            entries = root.findall('entry')
            if not entries:
                # 尝试带命名空间
                for entry in root.findall('.//atom:entry', ns) or root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                    paper = self._parse_entry(entry)
                    if paper:
                        papers.append(paper)
            else:
                for entry in entries:
                    paper = self._parse_entry(entry)
                    if paper:
                        papers.append(paper)

        except ET.ParseError as e:
            logger.error(f"arXiv XML解析错误: {e}")
        except Exception as e:
            logger.error(f"arXiv解析异常: {e}")

        return papers

    def _parse_entry(self, entry) -> Optional[Dict]:
        """解析单个entry元素"""
        try:
            paper = {
                'paperId': '',
                'title': '',
                'abstract': '',
                'authors': [],
                'year': None,
                'published': '',
                'updated': '',
                'categories': [],
                'comment': '',
                'journal_ref': '',
                'doi': '',
                'pdf_url': '',
                'source': 'arxiv',
                'citationCount': 0,
                'quality_score': 0,
            }

            # 标题
            title_elem = entry.find('title')
            if title_elem is not None and title_elem.text:
                paper['title'] = ' '.join(title_elem.text.split())

            # 摘要
            summary_elem = entry.find('summary')
            if summary_elem is not None and summary_elem.text:
                paper['abstract'] = ' '.join(summary_elem.text.split())

            # 作者
            authors = []
            for author in entry.findall('author'):
                name_elem = author.find('name')
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text)
            paper['authors'] = authors

            # 发布日期
            published_elem = entry.find('published')
            if published_elem is not None and published_elem.text:
                paper['published'] = published_elem.text
                try:
                    paper['year'] = int(published_elem.text[:4])
                except:
                    pass

            # 更新日期
            updated_elem = entry.find('updated')
            if updated_elem is not None and updated_elem.text:
                paper['updated'] = updated_elem.text

            # 分类/标签
            categories = []
            for category in entry.findall('category'):
                term = category.get('term')
                if term:
                    categories.append(term)
            paper['categories'] = categories

            # 评论
            comment_elem = entry.find('{http://arxiv.org/schemas/atom}comment')
            if comment_elem is None:
                comment_elem = entry.find('arxiv:comment')
            if comment_elem is not None and comment_elem.text:
                paper['comment'] = comment_elem.text

            # 期刊引用
            journal_ref_elem = entry.find('{http://arxiv.org/schemas/atom}journal_ref')
            if journal_ref_elem is None:
                journal_ref_elem = entry.find('arxiv:journal_ref')
            if journal_ref_elem is not None and journal_ref_elem.text:
                paper['journal_ref'] = journal_ref_elem.text

            # DOI
            doi_elem = entry.find('{http://arxiv.org/schemas/atom}doi')
            if doi_elem is None:
                doi_elem = entry.find('arxiv:doi')
            if doi_elem is not None and doi_elem.text:
                paper['doi'] = doi_elem.text

            # PDF链接
            for link in entry.findall('link'):
                if link.get('title') == 'pdf' or link.get('type') == 'application/pdf':
                    paper['pdf_url'] = link.get('href', '')
                    break

            # 使用arxiv ID作为paperId
            id_elem = entry.find('id')
            if id_elem is not None and id_elem.text:
                arxiv_id = id_elem.text.split('/')[-1]
                paper['paperId'] = arxiv_id

            return paper

        except Exception as e:
            logger.error(f"解析entry失败: {e}")
            return None

    async def search(self, query: str, max_results: int = 100) -> List[Dict]:
        """搜索arXiv文献"""
        await self.init_session()

        papers = []
        try:
            # 构建搜索查询
            search_query = query.replace(' ', '+')

            params = {
                "search_query": f"all:{search_query}",
                "start": 0,
                "max_results": min(max_results, 1000),  # arXiv最大1000
                "sortBy": "relevance",
                "sortOrder": "descending",
            }

            logger.info(f"正在搜索arXiv: {query}")

            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    text = await response.text()
                    papers = self._parse_arxiv_xml(text)
                    logger.success(f"从arXiv获取到 {len(papers)} 篇文献")
                else:
                    logger.warning(f"arXiv请求失败: HTTP {response.status}")

        except aiohttp.ClientError as e:
            logger.error(f"arXiv网络请求错误: {e}")
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
                "retmax": min(max_results, 10000),  # PubMed最大10000
                "retmode": "json",
                "usehistory": "n",
            }

            if self.api_key:
                params["api_key"] = self.api_key

            logger.info(f"正在搜索PubMed: {query}")

            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    id_list = data.get("esearchresult", {}).get("idlist", [])

                    logger.info(f"PubMed找到 {len(id_list)} 个结果")

                    # 第二步：获取详细信息
                    if id_list:
                        papers = await self._fetch_details(id_list)

                    logger.success(f"从PubMed获取到 {len(papers)} 篇文献")
                else:
                    logger.warning(f"PubMed请求失败: HTTP {response.status}")

        except aiohttp.ClientError as e:
            logger.error(f"PubMed网络请求错误: {e}")
        except Exception as e:
            logger.error(f"PubMed搜索出错: {e}")

        return papers

    async def _fetch_details(self, id_list: List[str]) -> List[Dict]:
        """获取文献详细信息"""
        papers = []

        # 分批获取，每批最多200个ID
        batch_size = 200
        for i in range(0, len(id_list), batch_size):
            batch = id_list[i:i + batch_size]
            batch_papers = await self._fetch_batch(batch)
            papers.extend(batch_papers)

            # 遵守API限制
            if len(id_list) > batch_size:
                await asyncio.sleep(0.34)  # PubMed API限制：每秒最多3次请求

        return papers

    async def _fetch_batch(self, id_list: List[str]) -> List[Dict]:
        """获取一批文献的详细信息"""
        papers = []

        try:
            fetch_url = f"{self.base_url}/efetch.fcgi"
            params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml",
                "rettype": "abstract",
            }

            if self.api_key:
                params["api_key"] = self.api_key

            async with self.session.get(fetch_url, params=params) as response:
                if response.status == 200:
                    text = await response.text()
                    papers = self._parse_pubmed_xml(text)

        except Exception as e:
            logger.error(f"获取PubMed详情出错: {e}")

        return papers

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict]:
        """解析PubMed XML响应"""
        papers = []

        try:
            root = ET.fromstring(xml_text)

            for pubmed_article in root.findall('PubmedArticle'):
                paper = self._parse_article(pubmed_article)
                if paper:
                    papers.append(paper)

        except ET.ParseError as e:
            logger.error(f"PubMed XML解析错误: {e}")
        except Exception as e:
            logger.error(f"PubMed解析异常: {e}")

        return papers

    def _parse_article(self, article) -> Optional[Dict]:
        """解析单个PubmedArticle"""
        try:
            medline_citation = article.find('MedlineCitation')
            if medline_citation is None:
                return None

            article_elem = medline_citation.find('Article')
            if article_elem is None:
                return None

            paper = {
                'paperId': '',
                'title': '',
                'abstract': '',
                'authors': [],
                'year': None,
                'month': None,
                'published': '',
                'journal': '',
                'volume': '',
                'issue': '',
                'pages': '',
                'pmid': '',
                'pmcid': '',
                'doi': '',
                'keywords': [],
                'mesh_terms': [],
                'source': 'pubmed',
                'citationCount': 0,
                'quality_score': 0,
            }

            # PMID
            pmid_elem = medline_citation.find('PMID')
            if pmid_elem is not None and pmid_elem.text:
                paper['pmid'] = pmid_elem.text
                paper['paperId'] = pmid_elem.text

            # 标题
            title_elem = article_elem.find('ArticleTitle')
            if title_elem is not None and title_elem.text:
                # 处理带有ELocationID的标题
                paper['title'] = ''.join(title_elem.text.split()) if isinstance(title_elem.text, str) else ''

            # 摘要
            abstract_elem = article_elem.find('Abstract')
            if abstract_elem is not None:
                abstract_parts = []
                for abstract_text in abstract_elem.findall('AbstractText'):
                    if abstract_text.text:
                        abstract_parts.append(abstract_text.text)
                paper['abstract'] = ' '.join(abstract_parts)

            # 作者
            author_list = article_elem.find('AuthorList')
            if author_list is not None:
                for author in author_list.findall('Author'):
                    last_name = author.find('LastName')
                    fore_name = author.find('ForeName')
                    if last_name is not None and last_name.text:
                        name = last_name.text
                        if fore_name is not None and fore_name.text:
                            name = f"{fore_name.text} {name}"
                        paper['authors'].append(name)

            # 发表日期
            journal = article_elem.find('Journal')
            if journal is not None:
                journal_info = journal.find('JournalInfo')
                if journal_info is not None:
                    journal_title = journal_info.find('MedlineTA')
                    if journal_title is not None and journal_title.text:
                        paper['journal'] = journal_title.text

                issue_info = journal.find('ISOAbbreviation') or journal.find('Title')
                if issue_info is not None and issue_info.text:
                    paper['journal'] = issue_info.text

                pub_date = journal.find('JournalPublicationDetails') or journal.find('PubDate')
                if pub_date is not None:
                    year_elem = pub_date.find('Year') or pub_date.find('MedlineDate')
                    month_elem = pub_date.find('Month')
                    day_elem = pub_date.find('Day')

                    year = None
                    if year_elem is not None and year_elem.text:
                        year_text = year_elem.text
                        # 处理 "2023" 或 "2023 Jan" 格式
                        if year_text:
                            try:
                                year = int(year_text[:4])
                            except ValueError:
                                pass
                            paper['year'] = year
                            if len(year_text) > 4:
                                paper['published'] = year_text
                            else:
                                month = month_elem.text[:3] if month_elem is not None and month_elem.text else ''
                                day = day_elem.text if day_elem is not None and day_elem.text else ''
                                paper['published'] = f"{year_text} {month} {day}".strip()

            # 处理ArticleDate作为备用
            if paper['year'] is None:
                article_date = article_elem.find('ArticleDate')
                if article_date is not None:
                    year_elem = article_date.find('Year')
                    if year_elem is not None and year_elem.text:
                        paper['year'] = int(year_elem.text[:4])

            # 卷期页
            volume_elem = journal.find('JournalIssue') if journal else None
            if volume_elem is not None:
                vol = volume_elem.find('Volume')
                iss = volume_elem.find('Issue')
                paper['volume'] = vol.text if vol is not None and vol.text else ''
                paper['issue'] = iss.text if iss is not None and iss.text else ''

            pages_elem = article_elem.find('Pagination') or article_elem.find('MedlinePgn')
            if pages_elem is not None:
                medline_pgn = pages_elem.find('MedlinePgn')
                if medline_pgn is not None and medline_pgn.text:
                    paper['pages'] = medline_pgn.text
                elif pages_elem.text:
                    paper['pages'] = pages_elem.text

            # DOI
            pubmed_data = article.find('PubmedData')
            if pubmed_data is not None:
                article_id_list = pubmed_data.find('ArticleIdList')
                if article_id_list is not None:
                    for article_id in article_id_list.findall('ArticleId'):
                        id_type = article_id.get('IdType')
                        if id_type == 'doi' and article_id.text:
                            paper['doi'] = article_id.text
                        elif id_type == 'pmc' and article_id.text:
                            paper['pmcid'] = article_id.text

            # PMC ID
            if not paper.get('pmcid'):
                if pubmed_data is not None:
                    article_id_list = pubmed_data.find('ArticleIdList')
                    if article_id_list is not None:
                        for article_id in article_id_list.findall('ArticleId'):
                            if article_id.get('IdType') == 'pmc':
                                paper['pmcid'] = article_id.text

            # Mesh词
            chemical_list = article_elem.find('ChemicalList')
            if chemical_list is not None:
                for chemical in chemical_list.findall('Chemical'):
                    substance = chemical.find('NameOfSubstance')
                    if substance is not None and substance.text:
                        paper['mesh_terms'].append(substance.text)

            return paper

        except Exception as e:
            logger.error(f"解析PubMed文章失败: {e}")
            return None


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
                "fields": "paperId,title,abstract,authors,year,citationCount,influentialCitationCount,venue,publicationDate,externalIds,openAccessPdf,url,fieldsOfStudy",
            }

            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            logger.info(f"正在搜索Semantic Scholar: {query}")

            # Semantic Scholar免费API每分钟100次请求限制
            request_count = 0
            max_requests_per_minute = 95

            while request_count < max_requests_per_minute:
                async with self.session.get(search_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        raw_papers = data.get("data", [])

                        for raw_paper in raw_papers:
                            paper = self._transform_paper(raw_paper)
                            if paper:
                                papers.append(paper)

                        # 处理分页
                        next_offset = data.get("next")
                        if not next_offset:
                            break

                        params["offset"] = next_offset
                        request_count += 1

                        # 遵守速率限制
                        await asyncio.sleep(0.7)  # 约85次/分钟

                    elif response.status == 429:
                        logger.warning("Semantic Scholar API限流，等待后重试...")
                        await asyncio.sleep(60)
                    else:
                        logger.warning(f"Semantic Scholar请求失败: HTTP {response.status}")
                        break

            logger.success(f"从Semantic Scholar获取到 {len(papers)} 篇文献")

        except aiohttp.ClientError as e:
            logger.error(f"Semantic Scholar网络请求错误: {e}")
        except Exception as e:
            logger.error(f"Semantic Scholar搜索出错: {e}")

        return papers

    def _transform_paper(self, raw_paper: Dict) -> Optional[Dict]:
        """转换Semantic Scholar论文格式"""
        try:
            authors = []
            for author in raw_paper.get("authors", []):
                if isinstance(author, str):
                    authors.append(author)
                elif isinstance(author, dict):
                    authors.append(author.get("name", ""))

            paper = {
                'paperId': raw_paper.get('paperId', ''),
                'title': raw_paper.get('title', ''),
                'abstract': raw_paper.get('abstract', ''),
                'authors': authors,
                'year': raw_paper.get('year'),
                'published': raw_paper.get('publicationDate', ''),
                'journal': raw_paper.get('venue', ''),
                'citationCount': raw_paper.get('citationCount', 0),
                'influentialCitationCount': raw_paper.get('influentialCitationCount', 0),
                'externalIds': raw_paper.get('externalIds', {}),
                'openAccessPdf': raw_paper.get('openAccessPdf', {}),
                'url': raw_paper.get('url', ''),
                'fieldsOfStudy': raw_paper.get('fieldsOfStudy', []),
                'source': 'semantic_scholar',
                'quality_score': 0,
            }

            # 添加DOI
            if paper.get('externalIds'):
                paper['doi'] = paper['externalIds'].get('DOI', '')

            # 添加PDF链接
            if paper.get('openAccessPdf'):
                paper['pdf_url'] = paper['openAccessPdf'].get('url', '')

            return paper

        except Exception as e:
            logger.error(f"转换Semantic Scholar论文失败: {e}")
            return None


class IEEESource(DataSource):
    """IEEE Xplore数据源"""

    def __init__(self):
        super().__init__("IEEE")
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
                "start_record": 1,
            }

            logger.info(f"正在搜索IEEE: {query}")

            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data.get("articles", [])

                    for article in articles:
                        paper = self._transform_ieee_paper(article)
                        if paper:
                            papers.append(paper)

                    logger.success(f"从IEEE获取到 {len(papers)} 篇文献")
                elif response.status == 403:
                    logger.warning("IEEE API密钥无效或已过期")
                elif response.status == 429:
                    logger.warning("IEEE API请求过于频繁")
                else:
                    logger.warning(f"IEEE请求失败: HTTP {response.status}")

        except aiohttp.ClientError as e:
            logger.error(f"IEEE网络请求错误: {e}")
        except Exception as e:
            logger.error(f"IEEE搜索出错: {e}")

        return papers

    def _transform_ieee_paper(self, article: Dict) -> Optional[Dict]:
        """转换IEEE论文格式"""
        try:
            authors = []
            for author in article.get("authors", {}).get("authors", []):
                if isinstance(author, dict):
                    authors.append(author.get("full_name", ""))
                elif isinstance(author, str):
                    authors.append(author)

            paper = {
                'paperId': article.get("article_number", ""),
                'title': article.get("title", ""),
                'abstract': article.get("abstract", ""),
                'authors': authors,
                'year': article.get("publication_year"),
                'published': f"{article.get('publication_year', '')} {article.get('publication_date', '')}",
                'journal': article.get("conference_info", "") or article.get("content_type", ""),
                'volume': article.get("volume", ""),
                'issue': article.get("issue", ""),
                'pages': f"{article.get('start_page', '')}-{article.get('end_page', '')}",
                'doi': article.get("doi", ""),
                'citationCount': 0,  # IEEE API不直接提供引用数
                'source': 'ieee',
                'quality_score': 0,
                'pdf_url': article.get("pdf_url", ""),
            }

            return paper

        except Exception as e:
            logger.error(f"转换IEEE论文失败: {e}")
            return None


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
        seen_ids = set()
        merged_papers = []

        # 优先级：Semantic Scholar > PubMed > arXiv > IEEE
        source_priority = {
            'semantic_scholar': 4,
            'pubmed': 3,
            'arxiv': 2,
            'ieee': 1,
        }

        for source_name, papers in results.items():
            priority = source_priority.get(source_name, 0)

            for paper in papers:
                # 使用多种标识符去重
                paper_id = paper.get("paperId", "")
                title = paper.get("title", "").lower().strip()

                # 优先使用paperId去重
                if paper_id and paper_id not in seen_ids:
                    seen_ids.add(paper_id)
                    paper["source"] = source_name
                    paper["source_priority"] = priority
                    merged_papers.append(paper)
                elif not paper_id and title and title not in seen_titles:
                    seen_titles.add(title)
                    paper["source"] = source_name
                    paper["source_priority"] = priority
                    merged_papers.append(paper)

        # 按来源优先级排序（保留更多信息的来源）
        merged_papers.sort(key=lambda x: x.get("source_priority", 0), reverse=True)

        logger.info(f"去重后共 {len(merged_papers)} 篇文献")
        return merged_papers

    def deduplicate_papers(self, results: Any) -> List[Dict]:
        """
        对搜索结果去重（兼容旧接口）

        Args:
            results: 搜索结果（可以是Dict或List）

        Returns:
            List[Dict]: 去重后的文献列表
        """
        if isinstance(results, dict):
            papers = results.get("papers", [])
            return papers
        elif isinstance(results, list):
            return results
        return []

    async def _close_all_sessions(self):
        """关闭所有HTTP会话"""
        for source in self.sources.values():
            await source.close_session()


# 创建全局搜索智能体实例
search_agent = SearchAgent()
