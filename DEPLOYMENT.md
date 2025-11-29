# AI4S-Discovery 部署指南

本文档提供详细的部署说明，适用于Windows 11笔记本环境。

## 目录

- [系统要求](#系统要求)
- [快速部署](#快速部署)
- [详细部署步骤](#详细部署步骤)
- [配置说明](#配置说明)
- [运行模式](#运行模式)
- [故障排除](#故障排除)

---

## 系统要求

### 最低配置
- **操作系统**: Windows 11
- **处理器**: Intel i5 或 AMD Ryzen 5（第8代及以上）
- **内存**: 16GB RAM
- **存储**: 20GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **操作系统**: Windows 11 Pro
- **处理器**: Intel i7 或 AMD Ryzen 7
- **内存**: 32GB RAM
- **显卡**: NVIDIA MX250 或更高（支持CUDA）
- **存储**: 50GB SSD
- **网络**: 100Mbps+

### 软件依赖
- Python 3.9+
- Git
- Docker Desktop（可选，用于容器化部署）

---

## 快速部署

### 方式1：一键安装脚本（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/AI4S-Discovery.git
cd AI4S-Discovery

# 2. 运行安装脚本
python scripts/init_project.py

# 3. 启动服务
python main.py
```

### 方式2：Docker部署

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/AI4S-Discovery.git
cd AI4S-Discovery

# 2. 构建并启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

---

## 详细部署步骤

### 步骤1：环境准备

#### 1.1 安装Python

从 [Python官网](https://www.python.org/downloads/) 下载Python 3.9+安装包。

安装时勾选 "Add Python to PATH"。

验证安装：
```bash
python --version
pip --version
```

#### 1.2 安装Git

从 [Git官网](https://git-scm.com/download/win) 下载Git安装包。

验证安装：
```bash
git --version
```

#### 1.3 安装Docker Desktop（可选）

从 [Docker官网](https://www.docker.com/products/docker-desktop) 下载Docker Desktop。

安装后启动Docker Desktop，确保WSL2后端已启用。

### 步骤2：克隆项目

```bash
# 克隆仓库
git clone https://github.com/yourusername/AI4S-Discovery.git

# 进入项目目录
cd AI4S-Discovery
```

### 步骤3：配置Python环境

#### 3.1 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows CMD
venv\Scripts\activate.bat

# Windows PowerShell
venv\Scripts\Activate.ps1

# Git Bash
source venv/Scripts/activate
```

#### 3.2 安装依赖

使用国内镜像源加速安装：

```bash
# 使用清华镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像源
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 步骤4：配置环境变量

#### 4.1 复制配置模板

```bash
copy .env.example .env
```

#### 4.2 编辑.env文件

使用文本编辑器打开`.env`文件，配置以下参数：

```env
# 项目基本配置
PROJECT_NAME=AI4S-Discovery
VERSION=1.0.0
ENVIRONMENT=production

# API密钥（可选）
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
PUBMED_EMAIL=your_email@example.com
IEEE_API_KEY=your_ieee_key_here

# 数据库配置
SQLITE_DB_PATH=./data/ai4s_discovery.db

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=./logs

# 硬件配置
DEVICE=auto  # auto/cpu/cuda
MAX_MEMORY_GB=12
ENABLE_GPU=true
```

### 步骤5：初始化项目

```bash
# 运行初始化脚本
python scripts/init_project.py
```

初始化脚本会：
- 创建必要的目录结构
- 初始化SQLite数据库
- 创建默认管理员账户
- 检测硬件配置
- 生成示例配置文件

### 步骤6：启动服务

根据需求选择启动方式：

#### 6.1 主程序模式

```bash
python main.py
```

#### 6.2 Web界面模式

```bash
streamlit run src/web/app.py
```

访问: http://localhost:8501

#### 6.3 API服务模式

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

访问API文档: http://localhost:8000/docs

#### 6.4 CLI命令行模式

```bash
# 搜索文献
python -m src.cli.main search "transformer attention mechanism"

# 完整分析
python -m src.cli.main analyze "钙钛矿太阳能电池" -o report.md

# 查看系统状态
python -m src.cli.main status
```

---

## 配置说明

### 数据源配置

在`config.yaml`中配置数据源：

```yaml
data_sources:
  arxiv:
    enabled: true
    max_results: 100
  semantic_scholar:
    enabled: true
    api_key: ""  # 可选
  pubmed:
    enabled: true
    email: "your_email@example.com"
  ieee:
    enabled: false
    api_key: ""  # 需要IEEE API Key
```

### 硬件配置

```yaml
hardware:
  device: "auto"  # auto/cpu/cuda
  max_memory_gb: 12
  enable_gpu: true
  gpu_memory_fraction: 0.8
```

### 智能体配置

```yaml
agents:
  coordinator:
    max_retries: 3
    timeout: 300
  search:
    concurrent_requests: 5
    cache_enabled: true
  analysis:
    quality_threshold: 40
    min_citations: 0
```

---

## 运行模式

### CPU模式

适用于无独立显卡的笔记本：

```bash
# 设置环境变量
set DEVICE=cpu

# 启动服务
python main.py
```

性能指标：
- 文献搜索: ~800ms/查询
- 质量评分: ~10ms/篇
- 假设生成: ~1.2s/假设

### GPU模式

适用于有NVIDIA显卡的笔记本（MX250及以上）：

```bash
# 设置环境变量
set DEVICE=cuda

# 启动服务
python main.py
```

性能指标：
- 文献搜索: ~300ms/查询
- 质量评分: ~3ms/篇
- 假设生成: ~300ms/假设

### 混合模式（推荐）

自动根据任务类型选择CPU或GPU：

```bash
# 设置环境变量
set DEVICE=auto

# 启动服务
python main.py
```

---

## Docker部署

### 构建镜像

```bash
docker build -t ai4s-discovery:latest .
```

### 使用docker-compose

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

### 单独运行容器

```bash
# 运行主服务
docker run -d \
  --name ai4s-discovery \
  -p 8000:8000 \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  ai4s-discovery:latest

# 查看日志
docker logs -f ai4s-discovery

# 进入容器
docker exec -it ai4s-discovery bash
```

---

## 7×24小时运行配置

### Windows任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：系统启动时
4. 操作：启动程序
   - 程序：`python.exe`
   - 参数：`C:\path\to\AI4S-Discovery\main.py`
   - 起始于：`C:\path\to\AI4S-Discovery`

### 电源管理

1. 打开"电源选项"
2. 选择"高性能"电源计划
3. 更改计划设置：
   - 关闭显示器：从不
   - 使计算机进入睡眠状态：从不

### 自动重启脚本

创建`scripts/watchdog.bat`：

```batch
@echo off
:loop
python main.py
echo Service crashed, restarting in 10 seconds...
timeout /t 10
goto loop
```

---

## 故障排除

### 问题1：导入模块失败

**错误信息**:
```
ModuleNotFoundError: No module named 'xxx'
```

**解决方案**:
```bash
# 重新安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2：GPU不可用

**错误信息**:
```
CUDA not available
```

**解决方案**:
1. 检查NVIDIA驱动是否安装
2. 安装CUDA Toolkit
3. 重新安装PyTorch:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 问题3：内存不足

**错误信息**:
```
MemoryError: Unable to allocate array
```

**解决方案**:
1. 减少`MAX_MEMORY_GB`配置
2. 降低`max_papers`参数
3. 启用分片加载模式

### 问题4：API限流

**错误信息**:
```
Rate limit exceeded
```

**解决方案**:
1. 配置API密钥
2. 降低并发请求数
3. 启用缓存机制

### 问题5：端口被占用

**错误信息**:
```
Address already in use
```

**解决方案**:
```bash
# 查找占用端口的进程
netstat -ano | findstr :8000

# 结束进程
taskkill /PID <进程ID> /F

# 或更改端口
uvicorn src.api.main:app --port 8001
```

---

## 性能优化建议

### 1. 使用SSD存储

将数据目录放在SSD上可显著提升I/O性能。

### 2. 启用缓存

在`config.yaml`中启用Redis缓存：

```yaml
cache:
  enabled: true
  backend: redis
  ttl: 3600
```

### 3. 调整并发数

根据网络带宽调整并发请求数：

```yaml
search:
  concurrent_requests: 5  # 100Mbps网络建议5-10
```

### 4. 定期清理日志

```bash
# 清理30天前的日志
forfiles /p logs /s /m *.log /d -30 /c "cmd /c del @path"
```

---

## 监控与维护

### 查看系统状态

```bash
python -m src.cli.main status
```

### 查看日志

```bash
# 实时查看日志
tail -f logs/ai4s_discovery.log

# Windows PowerShell
Get-Content logs/ai4s_discovery.log -Wait
```

### 数据库备份

```bash
# 备份SQLite数据库
copy data\ai4s_discovery.db data\backup\ai4s_discovery_backup_%date%.db
```

### 性能监控

访问Prometheus监控面板（如已配置）：
http://localhost:9090

---

## 更新升级

### 更新代码

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
python main.py
```

### 数据库迁移

```bash
# 备份数据库
copy data\ai4s_discovery.db data\ai4s_discovery_backup.db

# 运行迁移脚本（如有）
python scripts/migrate_database.py
```

---

## 安全建议

1. **修改默认密码**: 首次登录后立即修改admin账户密码
2. **启用HTTPS**: 生产环境建议配置SSL证书
3. **限制访问**: 配置防火墙规则，仅允许必要的IP访问
4. **定期备份**: 每周备份数据库和配置文件
5. **更新依赖**: 定期更新Python包以修复安全漏洞

---

## 技术支持

- **GitHub Issues**: https://github.com/yourusername/AI4S-Discovery/issues
- **文档**: https://ai4s-discovery.readthedocs.io
- **邮箱**: support@ai4s-discovery.com

---

## 许可证

本项目采用 Apache License 2.0 开源许可证。详见 [LICENSE](LICENSE) 文件。