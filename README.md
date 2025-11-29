# AI4S-Discovery

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2011-blue.svg)](https://www.microsoft.com/windows)

**AI4S-Discovery** 是一款基于多智能体架构的科研创新辅助工具，专为科研人员设计，能够自动化完成文献挖掘、研究脉络分析、技术成熟度评估和创新假设生成等全流程任务。

## 🌟 核心特性

### 核心功能
- **知识图谱构建**：基于NetworkX构建文献引用关系图谱，支持社区检测和中心性分析
- **技术成熟度（TRL）评估**：自动评估研究方向的成熟度（1-9级），采用多方法融合策略
- **LLM驱动的创新假设生成**：集成OpenAI GPT和本地MiniCPM模型，通过反事实推理生成创新假设
- **智能反事实推理**：分析不同条件下的研究结果，评估风险和成功概率
- **跨域知识迁移推荐**：基于图谱分析和LLM推理，推荐跨领域方法迁移

### 技术特点
- **多智能体架构**：搜索、分析、关联、评估、生成智能体协同工作
- **多源文献聚合**：支持arXiv、PubMed、Semantic Scholar等学术数据源
- **异步处理**：基于asyncio的高效异步架构
- **智能降级**：无API密钥时自动切换到模拟模式，保证系统可用

### 部署支持
- **灵活部署**：支持Windows本地部署，提供Docker容器化方案
- **API接口**：提供RESTful API，支持程序化调用
- **多格式报告**：支持Markdown、HTML格式报告生成
- **配置灵活**：支持CPU/GPU模式，本地模型/云端API可选

## 🚀 快速开始

### 系统要求

- **操作系统**：Windows 11
- **处理器**：Intel i5 及以上（支持CPU运行）
- **显卡**：NVIDIA MX250 及以上（可选，支持GPU加速）
- **内存**：16GB RAM
- **硬盘**：至少20GB可用空间
- **Python**：3.8 或更高版本

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/AI4S-Discovery.git
cd AI4S-Discovery
```

2. **创建虚拟环境**
```bash
python -m venv venv
venv\Scripts\activate
```

3. **安装依赖**（使用国内镜像源加速）
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

4. **配置环境变量**
```bash
copy .env.example .env
# 编辑 .env 文件，配置必要的参数
# 重要：配置OpenAI API密钥以启用LLM功能
# OPENAI_API_KEY=your_api_key_here
```

5. **下载模型（可选，用于本地LLM）**
```bash
python scripts/download_models.py
```

6. **初始化数据库**
```bash
python scripts/init_database.py
```

7. **启动服务**
```bash
# Web界面模式
python main.py --mode web

# API服务模式
python main.py --mode api

# 命令行模式
python main.py --mode cli
```

### Docker部署（推荐）

```bash
# 构建镜像
docker build -t ai4s-discovery .

# 运行容器
docker run -d -p 8501:8501 -p 8000:8000 -v ./data:/app/data ai4s-discovery
```

## 📖 使用示例

### 1. 通过Web界面使用

访问 `http://localhost:8501`，在界面中输入研究需求：

```
探索阿尔茨海默病免疫代谢靶点，需跨域文献支撑
```

系统将自动完成：
- 全网学术数据源检索（arXiv, PubMed, IEEE等）
- 构建研究演进图谱
- 评估技术成熟度
- 生成创新假设
- 输出综合报告

### 2. 通过API调用

```python
import requests

# 提交研究任务
response = requests.post('http://localhost:8000/api/v1/research/submit', json={
    'query': '钙钛矿太阳能电池稳定性研究',
    'domains': ['materials_science', 'energy'],
    'depth': 'comprehensive'
})

task_id = response.json()['task_id']

# 查询任务状态
status = requests.get(f'http://localhost:8000/api/v1/research/status/{task_id}')

# 获取结果
result = requests.get(f'http://localhost:8000/api/v1/research/result/{task_id}')
```

### 3. 通过Python SDK使用

```python
from src.agents.coordinator_agent import coordinator, ResearchTask

# 创建研究任务
task = ResearchTask(
    task_id='task_001',
    query='探索二维材料在芯片散热中的应用',
    domains=['materials_science', 'thermal_engineering'],
    depth='comprehensive',
    include_patents=True,
    generate_hypotheses=True,  # 启用LLM驱动的假设生成
    trl_assessment=True
)

# 提交任务
task_id = await coordinator.submit_task(task)

# 查询任务状态
status = coordinator.get_task_status(task_id)
print(f"进度: {status['progress']*100:.1f}%")

# 获取结果
result = coordinator.get_task_result(task_id)

# 结果包含：
# - literature: 文献搜索结果
# - analysis: 质量分析和趋势
# - knowledge_graph: 知识图谱
# - trl_assessment: TRL评估
# - innovations: 创新假设、反事实推理、跨域迁移
# - report: 生成的报告路径
```

### 4. LLM配置选项

```python
# 方式1: 使用OpenAI API（推荐）
# 在.env文件中配置：
# OPENAI_API_KEY=your_api_key_here
# OPENAI_MODEL=gpt-3.5-turbo
# LLM_PROVIDER=openai

# 方式2: 使用本地模型
# 在.env文件中配置：
# USE_LOCAL_MODEL=True
# LOCAL_MODEL_PATH=./models/minicpm
# LLM_PROVIDER=local

# 方式3: 无API密钥模式（自动降级）
# 系统会自动使用模拟模式，仍可运行但功能受限
```

## 🎯 核心功能详解

### 1. 智能文献搜索与分析
- **多源聚合**: 支持arXiv、PubMed、Semantic Scholar等主流学术数据库
- **智能去重**: 基于标题相似度的高效去重算法
- **质量评分**: 多维度评分（引用数、作者、期刊、年份）
- **关键词提取**: TF-IDF算法提取研究热点
- **趋势分析**: 年度分布、高产作者、研究演进

### 2. 知识图谱构建
- **图谱构建**: NetworkX构建有向引用图
- **社区检测**: Louvain算法识别研究社区
- **中心性分析**: 度中心性、介数中心性、PageRank
- **关键节点**: 自动识别领域内的重要文献

### 3. TRL技术成熟度评估
- **9级评估**: TRL 1-9级精确评估
- **多方法融合**: 关键词匹配、实验阶段识别、时间演进分析
- **可行性分析**: 技术、资源、时间三维评估
- **里程碑规划**: 自动生成技术发展路线图

### 4. LLM驱动的创新生成
- **假设生成**: 基于研究空白，LLM生成创新假设
- **反事实推理**: 分析不同条件下的可能结果
- **风险评估**: 识别潜在风险和成功概率
- **资源估算**: 自动估算所需资金、人力、时间
- **跨域迁移**: 推荐知识迁移方案和实施步骤

### 5. 智能报告生成
- **多格式输出**: Markdown、HTML、PDF（规划中）
- **结构化内容**: 文献统计、分析结果、图谱、TRL、假设、反事实
- **可视化**: 表格、图表、关键词云
- **自定义模板**: 支持自定义报告结构

## 📊 参考性能指标

以下为开发环境测试数据，实际性能取决于硬件配置和网络环境：

| 指标 | 典型值 | 说明 |
|------|--------|------|
| 文献搜索 | 50-100篇/次 | 取决于数据源API限制 |
| 质量分析 | 100篇/分钟 | 包含评分和关键词提取 |
| 图谱构建 | 1000节点/分钟 | NetworkX + Louvain算法 |
| LLM假设生成 | 2-10秒/假设 | 取决于LLM提供商和网络 |
| 反事实推理 | 5-15秒/场景 | LLM驱动的多场景分析 |
| 报告生成 | 1-3秒 | Markdown/HTML格式 |
| 内存占用 | 8-12GB | 取决于数据量和模型 |

**注意**：性能数据仅供参考，实际使用中会受到多种因素影响。

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详情。

## 📄 开源许可

本项目采用 [Apache License 2.0](./LICENSE) 开源许可证。

## 📞 联系方式

- **项目主页**：https://github.com/bingdongni/AI4S-Discovery
- **问题反馈**：https://github.com/bingdongni/AI4S-Discovery/issues
---

**注意**：本项目为单人开发的全功能科研辅助工具，专为Windows 11环境优化，支持CPU/GPU双模式运行。
