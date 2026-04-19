# 贡献指南

感谢您对 AI4S-Discovery 项目的关注！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告Bug

如果您发现了bug，请通过 [GitHub Issues](https://github.com/bingdongni/AI4S-Discovery/issues) 提交，并包含以下信息：

- Bug的详细描述
- 复现步骤
- 预期行为
- 实际行为
- 系统环境（操作系统、Python版本、硬件配置）
- 相关日志或截图

### 提出新功能

如果您有新功能建议，请：

1. 先检查是否已有类似的Issue
2. 创建新Issue，描述功能需求和使用场景
3. 等待维护者反馈

### 提交代码

1. **Fork项目**
   ```bash
   # 在GitHub上Fork项目
   # 克隆您的Fork
   git clone https://github.com/bingdongni/AI4S-Discovery.git
   cd AI4S-Discovery
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **开发与测试**
   ```bash
   # 安装开发依赖
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   
   # 运行测试
   pytest tests/
   
   # 检查代码风格
   flake8 src/
   black src/
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   # 或
   git commit -m "fix: 修复bug描述"
   ```

5. **推送并创建Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # 在GitHub上创建Pull Request
   ```

## 📝 代码规范

### Python代码风格

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 使用 `black` 格式化代码
- 使用 `flake8` 检查代码质量
- 函数和类必须有文档字符串

### 提交信息规范

使用语义化提交信息：

- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: 添加专利数据源支持
fix: 修复内存泄漏问题
docs: 更新API文档
```

## 🧪 测试要求

- 新功能必须包含单元测试
- 测试覆盖率应≥80%
- 所有测试必须通过

## 📚 文档要求

- 新功能需要更新相关文档
- API变更需要更新API文档
- 复杂功能需要提供使用示例

## 🌟 贡献者

感谢所有贡献者！

## 📄 许可证

贡献的代码将采用 Apache 2.0 许可证。