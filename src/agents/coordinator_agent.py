#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
协调智能体（Coordinator Agent）
负责任务分解、智能体调度和结果整合
基于微舆架构的多智能体协作模式
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from enum import Enum

from src.core.config import settings
from src.utils.device_manager import device_manager
from src.agents.search_agent import search_agent
from src.agents.analysis_agent import analysis_agent
from src.agents.relation_agent import relation_agent
from src.agents.evaluate_agent import evaluate_agent
from src.agents.generate_agent import generate_agent
from src.database.sqlite_manager import db_manager
from src.utils.report_generator import report_generator


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class ResearchTask:
    """研究任务类"""
    
    def __init__(
        self,
        task_id: str,
        query: str,
        domains: Optional[List[str]] = None,
        depth: str = "comprehensive",
        include_patents: bool = False,
        generate_hypotheses: bool = True,
        trl_assessment: bool = True,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ):
        self.task_id = task_id
        self.query = query
        self.domains = domains or []
        self.depth = depth
        self.include_patents = include_patents
        self.generate_hypotheses = generate_hypotheses
        self.trl_assessment = trl_assessment
        self.priority = priority
        
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        self.results: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.progress: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "query": self.query,
            "domains": self.domains,
            "depth": self.depth,
            "include_patents": self.include_patents,
            "generate_hypotheses": self.generate_hypotheses,
            "trl_assessment": self.trl_assessment,
            "priority": self.priority.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "errors": self.errors,
        }


class CoordinatorAgent:
    """
    协调智能体
    
    核心职责：
    1. 接收用户研究需求，解析并分解为子任务
    2. 调度专业智能体执行子任务
    3. 监控任务执行进度和资源使用
    4. 整合各智能体的结果
    5. 处理异常和失败重试
    """
    
    def __init__(self):
        """初始化协调智能体"""
        self.tasks: Dict[str, ResearchTask] = {}
        self.active_agents: Dict[str, Any] = {}
        
        logger.info("协调智能体初始化完成")
    
    async def submit_task(self, task: ResearchTask) -> str:
        """
        提交研究任务
        
        Args:
            task: 研究任务对象
        
        Returns:
            str: 任务ID
        """
        self.tasks[task.task_id] = task
        logger.info(f"任务已提交: {task.task_id} - {task.query}")
        
        # 异步执行任务
        asyncio.create_task(self._execute_task(task))
        
        return task.task_id
    
    async def _execute_task(self, task: ResearchTask):
        """
        执行研究任务
        
        Args:
            task: 研究任务对象
        """
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            logger.info(f"开始执行任务: {task.task_id}")
            
            # 阶段1: 需求解析与理解 (10%)
            await self._parse_requirements(task)
            task.progress = 0.1
            
            # 阶段2: 文献搜索与采集 (30%)
            await self._search_literature(task)
            task.progress = 0.4
            
            # 阶段3: 文献分析与质量评分 (20%)
            await self._analyze_literature(task)
            task.progress = 0.6
            
            # 阶段4: 知识图谱构建 (15%)
            await self._build_knowledge_graph(task)
            task.progress = 0.75
            
            # 阶段5: TRL评估（如果需要） (5%)
            if task.trl_assessment:
                await self._assess_trl(task)
            task.progress = 0.8
            
            # 阶段6: 创新假设生成和反事实推理（如果需要） (10%)
            if task.generate_hypotheses:
                await self._generate_innovations(task)
            task.progress = 0.9
            
            # 阶段7: 报告生成 (10%)
            await self._generate_report(task)
            task.progress = 1.0
            
            # 任务完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            duration = (task.completed_at - task.started_at).total_seconds()
            logger.success(f"任务完成: {task.task_id} (耗时: {duration:.2f}秒)")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.errors.append(str(e))
            logger.error(f"任务执行失败: {task.task_id} - {e}")
    
    async def _parse_requirements(self, task: ResearchTask):
        """
        解析研究需求
        
        Args:
            task: 研究任务对象
        """
        logger.info(f"[{task.task_id}] 阶段1: 解析研究需求")
        
        # 这里会调用NLP模型解析用户查询
        # 提取关键词、研究领域、时间范围等
        
        task.results["parsed_query"] = {
            "keywords": [],  # 从查询中提取的关键词
            "domains": task.domains,
            "time_range": None,
            "research_type": "exploratory",
        }
        
        await asyncio.sleep(0.5)  # 模拟处理时间
    
    async def _search_literature(self, task: ResearchTask):
        """
        搜索文献
        
        Args:
            task: 研究任务对象
        """
        logger.info(f"[{task.task_id}] 阶段2: 搜索文献")
        
        try:
            # 调用搜索智能体
            search_results = await search_agent.search(
                query=task.query,
                sources=['arxiv', 'pubmed', 'semantic_scholar'] if not task.include_patents else ['arxiv', 'pubmed', 'semantic_scholar'],
                max_results=100 if task.depth == 'comprehensive' else 50,
            )
            
            # 去重
            unique_papers = search_agent.deduplicate_papers(search_results)
            
            # 保存到数据库缓存
            for paper in unique_papers:
                try:
                    db_manager.cache_paper(paper)
                except Exception as e:
                    logger.warning(f"缓存文献失败: {e}")
            
            task.results["literature"] = {
                "total_papers": len(unique_papers),
                "sources": {source: len(papers) for source, papers in search_results.items()},
                "papers": unique_papers,
            }
            
            logger.success(f"搜索完成，共找到 {len(unique_papers)} 篇文献")
            
        except Exception as e:
            logger.error(f"文献搜索失败: {e}")
            task.results["literature"] = {
                "total_papers": 0,
                "sources": {},
                "papers": [],
                "error": str(e),
            }
    
    async def _analyze_literature(self, task: ResearchTask):
        """
        分析文献
        
        Args:
            task: 研究任务对象
        """
        logger.info(f"[{task.task_id}] 阶段3: 分析文献")
        
        try:
            papers = task.results.get("literature", {}).get("papers", [])
            
            if not papers:
                logger.warning("没有文献可供分析")
                task.results["analysis"] = {
                    "quality_scores": {},
                    "keywords": [],
                    "trends": {},
                    "key_findings": [],
                }
                return
            
            # 调用分析智能体
            analysis_results = await analysis_agent.analyze_papers(
                papers=papers,
                extract_keywords=True,
                calculate_quality=True,
                analyze_trends=True,
            )
            
            # 过滤高质量文献
            min_score = settings.PAPER_QUALITY_THRESHOLD
            high_quality_papers = analysis_agent.filter_by_quality(
                analysis_results['papers_with_scores'],
                min_score=min_score
            )
            
            # 提取关键发现
            key_findings = analysis_agent.extract_key_findings(
                high_quality_papers,
                top_n=10
            )
            
            task.results["analysis"] = {
                "total_analyzed": len(papers),
                "high_quality_count": len(high_quality_papers),
                "quality_threshold": min_score,
                "statistics": analysis_results['statistics'],
                "keywords": analysis_results['keywords'][:20],  # 前20个关键词
                "trends": analysis_results['trends'],
                "key_findings": key_findings,
            }
            
            # 更新文献列表为高质量文献
            task.results["literature"]["papers"] = high_quality_papers
            
            logger.success(f"分析完成，{len(high_quality_papers)} 篇高质量文献")
            
        except Exception as e:
            logger.error(f"文献分析失败: {e}")
            task.results["analysis"] = {
                "error": str(e),
            }
    
    async def _build_knowledge_graph(self, task: ResearchTask):
        """
        构建知识图谱
        
        Args:
            task: 研究任务对象
        """
        logger.info(f"[{task.task_id}] 阶段4: 构建知识图谱")
        
        try:
            papers = task.results.get("literature", {}).get("papers", [])
            
            if not papers:
                logger.warning("没有文献可供构建图谱")
                task.results["knowledge_graph"] = {
                    "nodes": 0,
                    "edges": 0,
                    "clusters": [],
                }
                return
            
            # 调用关联智能体构建知识图谱
            graph_result = await relation_agent.build_knowledge_graph(
                papers=papers,
                include_citations=True,
                include_similarity=True,
                max_nodes=settings.GRAPH_MAX_NODES if len(papers) > 1000 else None,
            )
            
            task.results["knowledge_graph"] = graph_result
            
            logger.success(
                f"知识图谱构建完成: {graph_result['nodes']}节点, "
                f"{graph_result['edges']}边, {len(graph_result['clusters'])}聚类"
            )
            
        except Exception as e:
            logger.error(f"知识图谱构建失败: {e}")
            task.results["knowledge_graph"] = {
                "nodes": 0,
                "edges": 0,
                "clusters": [],
                "error": str(e),
            }
    
    async def _assess_trl(self, task: ResearchTask):
        """
        评估技术成熟度
        
        Args:
            task: 研究任务对象
        """
        logger.info(f"[{task.task_id}] 阶段5: TRL评估")
        
        try:
            papers = task.results.get("literature", {}).get("papers", [])
            analysis = task.results.get("analysis", {})
            
            if not papers:
                logger.warning("没有文献可供TRL评估")
                task.results["trl_assessment"] = {
                    "level": 0,
                    "confidence": 0.0,
                    "evidence": [],
                }
                return
            
            # 调用评估智能体进行TRL评估
            trl_result = await evaluate_agent.assess_trl(
                papers=papers,
                query=task.query,
                analysis_results=analysis,
            )
            
            # 评估技术可行性
            feasibility = evaluate_agent.assess_feasibility(
                trl_result=trl_result,
                analysis_results=analysis,
            )
            
            task.results["trl_assessment"] = trl_result
            task.results["feasibility"] = feasibility
            
            logger.success(
                f"TRL评估完成: Level {trl_result['level']} "
                f"(置信度: {trl_result['confidence']:.2%})"
            )
            
        except Exception as e:
            logger.error(f"TRL评估失败: {e}")
            task.results["trl_assessment"] = {
                "level": 0,
                "confidence": 0.0,
                "evidence": [],
                "error": str(e),
            }
    
    async def _generate_innovations(self, task: ResearchTask):
        """
        生成创新建议（假设生成 + 反事实推理）
        
        Args:
            task: 研究任务对象
        """
        logger.info(f"[{task.task_id}] 阶段6: 生成创新建议（LLM驱动）")
        
        try:
            papers = task.results.get("literature", {}).get("papers", [])
            analysis = task.results.get("analysis", {})
            graph = task.results.get("knowledge_graph", {})
            trl = task.results.get("trl_assessment", {})
            
            if not papers:
                logger.warning("没有文献可供生成假设")
                task.results["innovations"] = {
                    "hypotheses": [],
                    "counterfactual_reasoning": [],
                    "cross_domain_transfers": [],
                }
                return
            
            # 从分析结果中提取研究空白
            research_gaps = self._extract_research_gaps(analysis, graph)
            
            # 调用生成智能体
            innovations = await generate_agent.generate_innovations(
                research_gaps=research_gaps,
                papers=papers,
                domains=task.domains,
                trl_results=[trl] if trl else None,
            )
            
            task.results["innovations"] = innovations
            
            logger.success(
                f"创新建议生成完成: {len(innovations.get('hypotheses', []))} 个假设, "
                f"{len(innovations.get('counterfactual_reasoning', []))} 个反事实分析, "
                f"{len(innovations.get('cross_domain_transfers', []))} 个跨域迁移"
            )
            
        except Exception as e:
            logger.error(f"创新建议生成失败: {e}")
            task.results["innovations"] = {
                "hypotheses": [],
                "counterfactual_reasoning": [],
                "cross_domain_transfers": [],
                "error": str(e),
            }
    
    def _extract_research_gaps(self, analysis: Dict, graph: Dict) -> List[Dict]:
        """
        从分析结果中提取研究空白
        
        Args:
            analysis: 分析结果
            graph: 知识图谱结果
        
        Returns:
            List[Dict]: 研究空白列表
        """
        gaps = []
        
        # 从关键词中识别研究不足的概念
        keywords = analysis.get('keywords', [])
        for kw in keywords[:10]:
            if kw.get('frequency', 0) < 5:  # 低频关键词可能是研究不足的领域
                gaps.append({
                    'type': 'under_researched_concept',
                    'concept': kw.get('term', ''),
                    'paper_count': kw.get('frequency', 0),
                    'priority': 'high' if kw.get('tfidf_score', 0) > 0.1 else 'medium',
                })
        
        # 从图谱社区中识别跨域机会
        communities = graph.get('communities', [])
        if len(communities) >= 2:
            for i in range(min(len(communities) - 1, 3)):
                comm1 = communities[i]
                comm2 = communities[i + 1]
                gaps.append({
                    'type': 'missing_cross_domain',
                    'concepts': [
                        comm1.get('topics', ['领域A'])[0],
                        comm2.get('topics', ['领域B'])[0],
                    ],
                    'priority': 'medium',
                })
        
        # 如果没有发现空白，创建默认空白
        if not gaps:
            gaps.append({
                'type': 'general_research_gap',
                'concept': '新兴研究方向',
                'priority': 'medium',
            })
        
        return gaps[:5]  # 最多返回5个研究空白
    
    async def _generate_report(self, task: ResearchTask):
        """
        生成研究报告
        
        Args:
            task: 研究任务对象
        """
        logger.info(f"[{task.task_id}] 阶段7: 生成报告")
        
        try:
            # 准备报告数据
            report_data = {
                "literature": task.results.get("literature", {}),
                "analysis": task.results.get("analysis", {}),
                "knowledge_graph": task.results.get("knowledge_graph", {}),
                "trl_assessment": task.results.get("trl_assessment", {}),
                "innovations": task.results.get("innovations", {}),
            }
            
            # 生成Markdown报告
            output_path = settings.REPORT_DIR / f"report_{task.task_id}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            report_generator.generate(
                result=report_data,
                output_path=str(output_path),
                format='markdown',
            )
            
            # 同时生成HTML版本
            html_path = settings.REPORT_DIR / f"report_{task.task_id}.html"
            report_generator.generate(
                result=report_data,
                output_path=str(html_path),
                format='html',
            )
            
            task.results["report"] = {
                "format": "markdown",
                "markdown_path": str(output_path),
                "html_path": str(html_path),
                "generated_at": datetime.now().isoformat(),
            }
            
            logger.success(f"报告已生成: {output_path}")
            
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            task.results["report"] = {
                "error": str(e),
            }
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            Optional[Dict]: 任务状态字典
        """
        task = self.tasks.get(task_id)
        if task:
            return task.to_dict()
        return None
    
    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
        
        Returns:
            Optional[Dict]: 任务结果字典
        """
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            return task.results
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            bool: 是否成功取消
        """
        task = self.tasks.get(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.status = TaskStatus.CANCELLED
            logger.info(f"任务已取消: {task_id}")
            return True
        return False


# 创建全局协调智能体实例
coordinator = CoordinatorAgent()
