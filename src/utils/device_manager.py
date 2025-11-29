#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设备管理器
负责CPU/GPU检测、动态切换和资源监控
"""

import os
import platform
import psutil
import torch
from typing import Dict, Optional
from loguru import logger


class DeviceManager:
    """设备管理器类"""
    
    def __init__(self):
        """初始化设备管理器"""
        self.device = self._detect_device()
        self.cpu_info = self._get_cpu_info()
        self.memory_info = self._get_memory_info()
        self.gpu_info = self._get_gpu_info() if self.has_cuda() else None
        
    def _detect_device(self) -> str:
        """
        检测可用设备
        
        Returns:
            str: 'cuda' 或 'cpu'
        """
        from src.core.config import settings
        
        if settings.DEVICE == "cpu":
            return "cpu"
        elif settings.DEVICE == "cuda":
            if torch.cuda.is_available():
                return "cuda"
            else:
                logger.warning("指定使用CUDA但未检测到GPU，回退到CPU模式")
                return "cpu"
        else:  # auto
            return "cuda" if torch.cuda.is_available() else "cpu"
    
    def has_cuda(self) -> bool:
        """
        检查是否有CUDA支持
        
        Returns:
            bool: 是否支持CUDA
        """
        return torch.cuda.is_available()
    
    def _get_cpu_info(self) -> Dict:
        """
        获取CPU信息
        
        Returns:
            Dict: CPU信息字典
        """
        return {
            "name": platform.processor() or "Unknown CPU",
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        }
    
    def _get_memory_info(self) -> Dict:
        """
        获取内存信息
        
        Returns:
            Dict: 内存信息字典
        """
        mem = psutil.virtual_memory()
        return {
            "total": mem.total / (1024 ** 3),  # GB
            "available": mem.available / (1024 ** 3),
            "used": mem.used / (1024 ** 3),
            "percent": mem.percent,
        }
    
    def _get_gpu_info(self) -> Optional[Dict]:
        """
        获取GPU信息
        
        Returns:
            Optional[Dict]: GPU信息字典，如果没有GPU则返回None
        """
        if not self.has_cuda():
            return None
        
        try:
            gpu_id = 0
            gpu_properties = torch.cuda.get_device_properties(gpu_id)
            
            return {
                "name": gpu_properties.name,
                "compute_capability": f"{gpu_properties.major}.{gpu_properties.minor}",
                "total_memory": gpu_properties.total_memory / (1024 ** 3),  # GB
                "multi_processor_count": gpu_properties.multi_processor_count,
            }
        except Exception as e:
            logger.error(f"获取GPU信息失败: {e}")
            return None
    
    def get_device_info(self) -> Dict:
        """
        获取完整的设备信息
        
        Returns:
            Dict: 设备信息字典
        """
        info = {
            "device": self.device,
            "has_gpu": self.has_cuda(),
            "cpu_name": self.cpu_info["name"],
            "cpu_cores": self.cpu_info["cores"],
            "cpu_threads": self.cpu_info["threads"],
            "total_memory": self.memory_info["total"],
            "available_memory": self.memory_info["available"],
        }
        
        if self.gpu_info:
            info.update({
                "gpu_name": self.gpu_info["name"],
                "gpu_memory": self.gpu_info["total_memory"],
                "gpu_compute_capability": self.gpu_info["compute_capability"],
            })
        
        return info
    
    def get_optimal_device(self, task_type: str = "default") -> str:
        """
        根据任务类型和当前负载选择最优设备
        
        Args:
            task_type: 任务类型 ('light', 'medium', 'heavy')
        
        Returns:
            str: 推荐的设备 ('cuda' 或 'cpu')
        """
        # 如果没有GPU，直接返回CPU
        if not self.has_cuda():
            return "cpu"
        
        # 检查当前资源使用情况
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = self.memory_info["percent"]
        
        # 检查GPU使用情况
        if self.has_cuda():
            try:
                gpu_memory_allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
                gpu_memory_reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)
                gpu_usage_percent = (gpu_memory_allocated / self.gpu_info["total_memory"]) * 100
            except:
                gpu_usage_percent = 0
        else:
            gpu_usage_percent = 0
        
        # 决策逻辑
        if task_type == "light":
            # 轻量任务优先使用CPU
            return "cpu"
        
        elif task_type == "medium":
            # 中等任务：如果CPU负载高，使用GPU
            if cpu_usage > 70:
                return "cuda" if gpu_usage_percent < 80 else "cpu"
            return "cpu"
        
        elif task_type == "heavy":
            # 重量任务优先使用GPU
            if gpu_usage_percent < 85:
                return "cuda"
            return "cpu"
        
        # 默认：根据当前负载自动选择
        if cpu_usage > 80 and gpu_usage_percent < 70:
            return "cuda"
        elif gpu_usage_percent > 85:
            return "cpu"
        
        return self.device
    
    def monitor_resources(self) -> Dict:
        """
        监控当前资源使用情况
        
        Returns:
            Dict: 资源使用情况
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        resources = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024 ** 3),
        }
        
        if self.has_cuda():
            try:
                gpu_memory_allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
                gpu_memory_reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)
                gpu_memory_total = self.gpu_info["total_memory"]
                
                resources.update({
                    "gpu_memory_allocated_gb": gpu_memory_allocated,
                    "gpu_memory_reserved_gb": gpu_memory_reserved,
                    "gpu_memory_total_gb": gpu_memory_total,
                    "gpu_memory_percent": (gpu_memory_allocated / gpu_memory_total) * 100,
                })
            except Exception as e:
                logger.warning(f"获取GPU资源使用情况失败: {e}")
        
        return resources
    
    def check_memory_available(self, required_gb: float) -> bool:
        """
        检查是否有足够的内存
        
        Args:
            required_gb: 需要的内存大小（GB）
        
        Returns:
            bool: 是否有足够内存
        """
        available = self.memory_info["available"]
        return available >= required_gb
    
    def clear_gpu_cache(self):
        """清理GPU缓存"""
        if self.has_cuda():
            try:
                torch.cuda.empty_cache()
                logger.info("GPU缓存已清理")
            except Exception as e:
                logger.error(f"清理GPU缓存失败: {e}")
    
    def set_device(self, device: str):
        """
        设置当前使用的设备
        
        Args:
            device: 设备名称 ('cuda' 或 'cpu')
        """
        if device == "cuda" and not self.has_cuda():
            logger.warning("尝试设置CUDA设备但GPU不可用，使用CPU")
            device = "cpu"
        
        self.device = device
        logger.info(f"设备已切换到: {device}")
    
    def get_torch_device(self) -> torch.device:
        """
        获取PyTorch设备对象
        
        Returns:
            torch.device: PyTorch设备对象
        """
        return torch.device(self.device)
    
    def optimize_for_inference(self):
        """优化推理性能"""
        if self.has_cuda():
            # 启用cudnn自动优化
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.enabled = True
            logger.info("已启用CUDA优化")
        
        # 设置线程数
        torch.set_num_threads(self.cpu_info["threads"])
        logger.info(f"PyTorch线程数设置为: {self.cpu_info['threads']}")


# 创建全局设备管理器实例
device_manager = DeviceManager()