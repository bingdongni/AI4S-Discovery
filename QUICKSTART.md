# 🚀 快速开始指南

本指南将帮助您在5分钟内启动AI4S-Discovery项目。

## 📋 前置要求

- Windows 11操作系统
- Python 3.8或更高版本
- 16GB RAM（推荐）
- 20GB可用磁盘空间

## 🔧 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/AI4S-Discovery.git
cd AI4S-Discovery
```

### 2. 创建虚拟环境

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

使用清华镜像源加速安装：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 配置环境变量

```bash
copy .env.example .env
```

使用文本编辑器打开`.env`文件，根据需要修改配置。最基本的配置：

```env
# 设备选择（auto会自动检测）
DEVICE=auto

# API密钥（开发环境可以使用默认值）
API_KEY=dev_api_key_change_in_production
```

## 🎮 运行项目

### 方式1: Web界面（推荐新手）

```bash
python main.py --mode web
```

然后在浏览器中访问：http://localhost:8501

### 方式2: API服务

```bash
python main.py --mode api
```

API文档地址：http://localhost:8000/docs

### 方式3: Docker部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 📝 第一次使用

### 通过Web界面

1. 访问 http://localhost:8501
2. 在「研究查询」标签页输入您的研究需求，例如：
   ```
   探索钙钛矿太阳能电池稳定性研究
   ```
3. 选择分析深度和其他选项
4. 点击「开始研究」按钮
5. 在「任务管理」标签页查看进度和结果

### 通过API

使用curl或任何HTTP客户端：

```bash
curl -X POST "http://localhost:8000/api/v1/research/submit" \
  -H "x-api-key: dev_api_key_change_in_production" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "钙钛矿太阳能电池稳定性研究",
    "depth": "comprehensive",
    "generate_hypotheses": true,
    "trl_assessment": true
  }'
```

### 通过Python SDK

```python
from src.agents import coordinator, ResearchTask, TaskPriority
import asyncio

# 创建任务
task = ResearchTask(
    task_id="test-001",
    query="钙钛矿太阳能电池稳定性研究",
    depth="comprehensive",
    generate_hypotheses=True,
    trl_assessment=True,
    priority=TaskPriority.MEDIUM
)

# 提交任务
async def main():
    await coordinator.submit_task(task)
    
    # 等待完成
    while True:
        status = coordinator.get_task_status(task.task_id)
        if status and status['status'] == 'completed':
            result = coordinator.get_task_result(task.task_id)
            print(result)
            break
        await asyncio.sleep(1)

asyncio.run(main())
```

## 🔍 验证安装

运行以下命令检查系统状态：

```bash
# 检查硬件配置
python -c "from src.utils import device_manager; print(device_manager.get_device_info())"

# 检查配置
python -c "from src.core import settings; print(f'Version: {settings.APP_VERSION}')"
```

## 🐛 常见问题

### 问题1: 导入错误

**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**: 确保已激活虚拟环境并安装了所有依赖
```bash
venv\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2: GPU不可用

**错误**: GPU未检测到

**解决**: 
1. 检查是否安装了CUDA和PyTorch GPU版本
2. 在`.env`中设置`DEVICE=cpu`强制使用CPU模式

### 问题3: 端口被占用

**错误**: `Address already in use`

**解决**: 修改`.env`中的端口配置
```env
API_PORT=8001
WEB_PORT=8502
```

### 问题4: 内存不足

**错误**: 内存溢出

**解决**: 
1. 关闭其他占用内存的程序
2. 在`.env`中降低内存限制
```env
MEMORY_LIMIT=8
```

## 📚 下一步

- 阅读 [README.md](./README.md) 了解完整功能
- 查看 [PROJECT_STATUS.md](./PROJECT_STATUS.md) 了解开发进度
- 访问 [API文档](http://localhost:8000/docs) 学习API使用
- 加入 [GitHub Discussions](https://github.com/yourusername/AI4S-Discovery/discussions) 参与讨论

## 💡 使用技巧

1. **首次运行较慢**: 第一次运行时需要下载模型，请耐心等待
2. **使用GPU加速**: 如果有NVIDIA显卡，系统会自动使用GPU加速
3. **批量处理**: 可以同时提交多个研究任务
4. **保存结果**: 所有结果会自动保存在`reports/`目录

## 🆘 获取帮助

- 查看 [文档](./docs/)
- 提交 [Issue](https://github.com/yourusername/AI4S-Discovery/issues)
- 发送邮件: your.email@example.com

---

**祝您使用愉快！** 🎉