#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prometheus监控集成
提供系统性能指标收集和监控
"""

import time
import psutil
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from loguru import logger

from src.utils.device_manager import device_manager


# 定义监控指标

# 请求计数器
request_counter = Counter(
    'ai4s_requests_total',
    'Total number of requests',
    ['endpoint', 'method', 'status']
)

# 请求延迟直方图
request_latency = Histogram(
    'ai4s_request_duration_seconds',
    'Request latency in seconds',
    ['endpoint', 'method']
)

# 文献处理计数器
paper_processed_counter = Counter(
    'ai4s_papers_processed_total',
    'Total number of papers processed',
    ['source']
)

# 任务状态计数器
task_counter = Counter(
    'ai4s_tasks_total',
    'Total number of tasks',
    ['status']
)

# 系统资源指标
cpu_usage_gauge = Gauge('ai4s_cpu_usage_percent', 'CPU usage percentage')
memory_usage_gauge = Gauge('ai4s_memory_usage_bytes', 'Memory usage in bytes')
memory_percent_gauge = Gauge('ai4s_memory_usage_percent', 'Memory usage percentage')
disk_usage_gauge = Gauge('ai4s_disk_usage_percent', 'Disk usage percentage')

# GPU指标（如果可用）
gpu_memory_gauge = Gauge('ai4s_gpu_memory_usage_bytes', 'GPU memory usage in bytes')
gpu_utilization_gauge = Gauge('ai4s_gpu_utilization_percent', 'GPU utilization percentage')

# 智能体指标
agent_execution_time = Histogram(
    'ai4s_agent_execution_seconds',
    'Agent execution time in seconds',
    ['agent_name']
)

# 数据库查询指标
db_query_counter = Counter(
    'ai4s_db_queries_total',
    'Total number of database queries',
    ['operation']
)

db_query_latency = Histogram(
    'ai4s_db_query_duration_seconds',
    'Database query latency in seconds',
    ['operation']
)


class MonitoringManager:
    """监控管理器"""
    
    def __init__(self):
        """初始化监控管理器"""
        self.start_time = time.time()
        logger.info("监控管理器初始化完成")
    
    def update_system_metrics(self):
        """更新系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_usage_gauge.set(cpu_percent)
            
            # 内存使用
            memory = psutil.virtual_memory()
            memory_usage_gauge.set(memory.used)
            memory_percent_gauge.set(memory.percent)
            
            # 磁盘使用
            disk = psutil.disk_usage('/')
            disk_usage_gauge.set(disk.percent)
            
            # GPU指标（如果可用）
            device_info = device_manager.get_device_info()
            if device_info['device_type'] == 'cuda':
                gpu_memory_used = device_info.get('gpu_memory_used', 0) * 1024 ** 3  # GB to bytes
                gpu_memory_gauge.set(gpu_memory_used)
                
                # GPU利用率（简化实现）
                gpu_utilization = (device_info.get('gpu_memory_used', 0) / 
                                 device_info.get('gpu_memory_total', 1)) * 100
                gpu_utilization_gauge.set(gpu_utilization)
            
        except Exception as e:
            logger.error(f"更新系统指标失败: {e}")
    
    def record_request(self, endpoint: str, method: str, status: int, duration: float):
        """
        记录请求
        
        Args:
            endpoint: 端点
            method: HTTP方法
            status: 状态码
            duration: 请求时长（秒）
        """
        request_counter.labels(endpoint=endpoint, method=method, status=str(status)).inc()
        request_latency.labels(endpoint=endpoint, method=method).observe(duration)
    
    def record_paper_processed(self, source: str, count: int = 1):
        """
        记录文献处理
        
        Args:
            source: 数据源
            count: 处理数量
        """
        paper_processed_counter.labels(source=source).inc(count)
    
    def record_task(self, status: str):
        """
        记录任务
        
        Args:
            status: 任务状态
        """
        task_counter.labels(status=status).inc()
    
    def record_agent_execution(self, agent_name: str, duration: float):
        """
        记录智能体执行
        
        Args:
            agent_name: 智能体名称
            duration: 执行时长（秒）
        """
        agent_execution_time.labels(agent_name=agent_name).observe(duration)
    
    def record_db_query(self, operation: str, duration: float):
        """
        记录数据库查询
        
        Args:
            operation: 操作类型
            duration: 查询时长（秒）
        """
        db_query_counter.labels(operation=operation).inc()
        db_query_latency.labels(operation=operation).observe(duration)
    
    def get_metrics(self) -> bytes:
        """
        获取Prometheus格式的指标
        
        Returns:
            指标数据
        """
        # 更新系统指标
        self.update_system_metrics()
        
        # 生成Prometheus格式
        return generate_latest(REGISTRY)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': round(uptime, 2),
            'uptime_hours': round(uptime / 3600, 2),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'device': device_manager.device,
        }


# 创建全局监控管理器实例
monitoring_manager = MonitoringManager()


# 便捷函数

def record_request(endpoint: str, method: str, status: int, duration: float):
    """记录请求"""
    monitoring_manager.record_request(endpoint, method, status, duration)


def record_paper_processed(source: str, count: int = 1):
    """记录文献处理"""
    monitoring_manager.record_paper_processed(source, count)


def record_task(status: str):
    """记录任务"""
    monitoring_manager.record_task(status)


def record_agent_execution(agent_name: str, duration: float):
    """记录智能体执行"""
    monitoring_manager.record_agent_execution(agent_name, duration)


def record_db_query(operation: str, duration: float):
    """记录数据库查询"""
    monitoring_manager.record_db_query(operation, duration)


def get_metrics() -> bytes:
    """获取指标"""
    return monitoring_manager.get_metrics()


def get_statistics() -> Dict[str, Any]:
    """获取统计信息"""
    return monitoring_manager.get_statistics()