#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Streamlit Web界面
提供用户友好的交互界面
"""

import streamlit as st
import asyncio
import uuid
from datetime import datetime

from src.core.config import settings
from src.agents.coordinator_agent import coordinator, ResearchTask, TaskPriority
from src.utils.device_manager import device_manager

# 页面配置
st.set_page_config(
    page_title="AI4S-Discovery",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """主函数"""
    
    # 标题
    st.markdown('<div class="main-header">🔬 AI4S-Discovery</div>', unsafe_allow_html=True)
    st.markdown("**科研创新辅助工具** - 基于多智能体架构的全流程研究支持系统")
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 系统信息")
        
        # 设备信息
        device_info = device_manager.get_device_info()
        st.subheader("硬件配置")
        st.write(f"**设备**: {device_info['device'].upper()}")
        st.write(f"**CPU**: {device_info['cpu_name']}")
        st.write(f"**内存**: {device_info['total_memory']:.1f} GB")
        
        if device_info['has_gpu']:
            st.write(f"**GPU**: {device_info['gpu_name']}")
            st.write(f"**GPU内存**: {device_info['gpu_memory']:.1f} GB")
        
        # 资源使用情况
        st.subheader("资源使用")
        resources = device_manager.monitor_resources()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("CPU", f"{resources['cpu_percent']:.1f}%")
        with col2:
            st.metric("内存", f"{resources['memory_percent']:.1f}%")
        
        if device_info['has_gpu']:
            st.metric("GPU内存", f"{resources.get('gpu_memory_percent', 0):.1f}%")
        
        st.divider()
        
        # 关于
        st.subheader("关于")
        st.write(f"**版本**: {settings.APP_VERSION}")
        st.write("**许可证**: Apache 2.0")
        st.write("[GitHub](https://github.com/bingdongni/AI4S-Discovery)")
    
    # 主内容区
    tab1, tab2, tab3 = st.tabs(["🔍 研究查询", "📊 任务管理", "📚 使用指南"])
    
    with tab1:
        research_query_tab()
    
    with tab2:
        task_management_tab()
    
    with tab3:
        usage_guide_tab()


def research_query_tab():
    """研究查询标签页"""
    st.header("研究查询")
    
    # 查询输入
    query = st.text_area(
        "请输入您的研究需求",
        placeholder="例如：探索阿尔茨海默病免疫代谢靶点，需跨域文献支撑",
        height=100,
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        domains = st.multiselect(
            "研究领域（可选）",
            ["生物医药", "材料科学", "人工智能", "能源", "化学", "物理"],
        )
        
        depth = st.selectbox(
            "分析深度",
            ["quick", "standard", "comprehensive"],
            index=2,
            format_func=lambda x: {"quick": "快速", "standard": "标准", "comprehensive": "全面"}[x]
        )
    
    with col2:
        include_patents = st.checkbox("包含专利分析", value=False)
        generate_hypotheses = st.checkbox("生成创新假设", value=True)
        trl_assessment = st.checkbox("TRL评估", value=True)
        
        priority = st.selectbox(
            "任务优先级",
            ["low", "medium", "high", "urgent"],
            index=1,
            format_func=lambda x: {"low": "低", "medium": "中", "high": "高", "urgent": "紧急"}[x]
        )
    
    # 提交按钮
    if st.button("🚀 开始研究", type="primary", use_container_width=True):
        if not query:
            st.error("请输入研究需求")
        else:
            with st.spinner("正在提交任务..."):
                task_id = submit_research_task(
                    query=query,
                    domains=domains,
                    depth=depth,
                    include_patents=include_patents,
                    generate_hypotheses=generate_hypotheses,
                    trl_assessment=trl_assessment,
                    priority=priority,
                )
                
                if task_id:
                    st.success(f"✅ 任务已提交！任务ID: `{task_id}`")
                    st.info("请在「任务管理」标签页查看进度")
                    
                    # 保存到session state
                    if 'tasks' not in st.session_state:
                        st.session_state.tasks = []
                    st.session_state.tasks.append(task_id)


def task_management_tab():
    """任务管理标签页"""
    st.header("任务管理")
    
    if 'tasks' not in st.session_state or not st.session_state.tasks:
        st.info("暂无任务")
        return
    
    # 显示所有任务
    for task_id in st.session_state.tasks:
        status = coordinator.get_task_status(task_id)
        
        if status:
            with st.expander(f"任务 {task_id[:8]}... - {status['status']}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**查询**: {status['query']}")
                    st.write(f"**状态**: {status['status']}")
                
                with col2:
                    st.write(f"**创建时间**: {status['created_at']}")
                    st.write(f"**优先级**: {status['priority']}")
                
                with col3:
                    st.progress(status['progress'], text=f"进度: {status['progress']*100:.0f}%")
                
                if status['status'] == 'completed':
                    if st.button(f"查看结果", key=f"view_{task_id}"):
                        result = coordinator.get_task_result(task_id)
                        if result:
                            st.json(result)
                
                elif status['status'] in ['pending', 'running']:
                    if st.button(f"取消任务", key=f"cancel_{task_id}"):
                        coordinator.cancel_task(task_id)
                        st.rerun()


def usage_guide_tab():
    """使用指南标签页"""
    st.header("使用指南")
    
    st.markdown("""
    ## 🎯 快速开始
    
    ### 1. 输入研究需求
    在「研究查询」标签页输入您的研究问题，例如：
    - "探索钙钛矿太阳能电池稳定性研究"
    - "分析二维材料在芯片散热中的应用"
    - "阿尔茨海默病免疫代谢靶点研究"
    
    ### 2. 配置参数
    - **研究领域**: 可选择一个或多个相关领域
    - **分析深度**: 
        - 快速：基础文献检索和分析
        - 标准：包含图谱构建和趋势分析
        - 全面：完整的研究报告，包含假设生成和TRL评估
    - **专利分析**: 是否包含专利数据
    - **创新假设**: 是否生成创新假设
    - **TRL评估**: 是否进行技术成熟度评估
    
    ### 3. 查看结果
    任务完成后，在「任务管理」标签页查看详细结果，包括：
    - 文献列表和质量评分
    - 研究演进图谱
    - 技术成熟度评估
    - 创新假设建议
    - 综合研究报告
    
    ## 📊 性能指标
    
    | 指标 | CPU模式 | GPU模式 |
    |------|---------|---------|
    | 查询延迟 | ≤800ms | ≤300ms |
    | 文献处理 | 5万篇/天 | 10万篇/天 |
    | 图谱构建 | 5秒/千节点 | 1.5秒/千节点 |
    
    ## 💡 使用技巧
    
    1. **精确查询**: 使用具体的研究问题可以获得更准确的结果
    2. **领域选择**: 选择相关领域可以提高搜索精度
    3. **深度选择**: 根据需求选择合适的分析深度
    4. **批量处理**: 可以同时提交多个任务
    
    ## 🔗 相关链接
    
    - [GitHub仓库](https://github.com/bingdongni/AI4S-Discovery)
    - [API文档](http://localhost:8000/docs)
    - [问题反馈](https://github.com/bingdongni/AI4S-Discovery/issues)
    """)


def submit_research_task(
    query: str,
    domains: list,
    depth: str,
    include_patents: bool,
    generate_hypotheses: bool,
    trl_assessment: bool,
    priority: str,
) -> str:
    """提交研究任务"""
    try:
        task_id = str(uuid.uuid4())
        
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT,
        }
        
        task = ResearchTask(
            task_id=task_id,
            query=query,
            domains=domains,
            depth=depth,
            include_patents=include_patents,
            generate_hypotheses=generate_hypotheses,
            trl_assessment=trl_assessment,
            priority=priority_map.get(priority, TaskPriority.MEDIUM),
        )
        
        # 使用asyncio运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coordinator.submit_task(task))
        
        return task_id
    
    except Exception as e:
        st.error(f"提交任务失败: {e}")
        return None


if __name__ == "__main__":
    main()