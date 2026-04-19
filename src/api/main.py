#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FastAPI主应用
提供RESTful API接口
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uuid

from src.core.config import settings
from src.agents.coordinator_agent import coordinator, ResearchTask, TaskPriority
from src.utils.device_manager import device_manager

# 创建FastAPI应用
app = FastAPI(
    title="AI4S-Discovery API",
    description="科研创新辅助工具API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 请求模型 ============

class ResearchRequest(BaseModel):
    """研究任务请求"""
    query: str
    domains: Optional[List[str]] = None
    depth: str = "comprehensive"
    include_patents: bool = False
    generate_hypotheses: bool = True
    trl_assessment: bool = True
    priority: str = "medium"


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str


# ============ 依赖项 ============

async def verify_api_key(x_api_key: str = Header(...)):
    """验证API密钥"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ============ 路由 ============

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "AI4S-Discovery API",
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    device_info = device_manager.get_device_info()
    resources = device_manager.monitor_resources()
    
    return {
        "status": "healthy",
        "device": device_info["device"],
        "cpu_usage": resources["cpu_percent"],
        "memory_usage": resources["memory_percent"],
    }


@app.post("/api/v1/research/submit", response_model=TaskResponse)
async def submit_research_task(
    request: ResearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    提交研究任务
    
    Args:
        request: 研究任务请求
        api_key: API密钥
    
    Returns:
        TaskResponse: 任务响应
    """
    try:
        # 创建任务
        task_id = str(uuid.uuid4())
        
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT,
        }
        
        task = ResearchTask(
            task_id=task_id,
            query=request.query,
            domains=request.domains,
            depth=request.depth,
            include_patents=request.include_patents,
            generate_hypotheses=request.generate_hypotheses,
            trl_assessment=request.trl_assessment,
            priority=priority_map.get(request.priority.lower(), TaskPriority.MEDIUM),
        )
        
        # 提交任务
        await coordinator.submit_task(task)
        
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message="任务已提交，正在处理中"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/research/status/{task_id}")
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        api_key: API密钥
    
    Returns:
        任务状态信息
    """
    status = coordinator.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return status


@app.get("/api/v1/research/result/{task_id}")
async def get_task_result(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    获取任务结果
    
    Args:
        task_id: 任务ID
        api_key: API密钥
    
    Returns:
        任务结果
    """
    result = coordinator.get_task_result(task_id)
    
    if not result:
        status = coordinator.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="任务不存在")
        elif status["status"] != "completed":
            raise HTTPException(status_code=400, detail="任务尚未完成")
        else:
            raise HTTPException(status_code=500, detail="无法获取任务结果")
    
    return result


@app.delete("/api/v1/research/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    取消任务
    
    Args:
        task_id: 任务ID
        api_key: API密钥
    
    Returns:
        取消结果
    """
    success = coordinator.cancel_task(task_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="无法取消任务")
    
    return {"message": "任务已取消"}


@app.get("/api/v1/system/info")
async def get_system_info(api_key: str = Depends(verify_api_key)):
    """
    获取系统信息
    
    Args:
        api_key: API密钥
    
    Returns:
        系统信息
    """
    device_info = device_manager.get_device_info()
    resources = device_manager.monitor_resources()
    
    return {
        "device": device_info,
        "resources": resources,
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )