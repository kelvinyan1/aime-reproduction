# 🤖 Aime多智能体框架原型

基于论文《Aime: Towards Fully-Autonomous Multi-Agent Framework》的原型实现，专注于核心概念验证。

## ✨ 特性

- **🧠 动态规划**: 基于LLM的实时任务分解和重规划
- **🏭 智能体工厂**: 根据任务特性动态创建专用智能体
- **🔄 ReAct执行**: 推理-行动-观察的智能体执行循环
- **📊 进度管理**: 集中式任务状态和执行历史管理
- **🤝 多智能体协作**: 支持多个智能体协同完成复杂任务

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保Python 3.9+
python --version

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.template .env
# 编辑.env文件，设置API密钥
```

### 2. 配置API密钥

在`.env`文件中设置：

### 3. 运行测试

```bash
# 完整测试套件
python test_cases.py

# 简单功能测试
python test_cases.py quick
```

### 4. 开始使用

```bash
# 命令行模式
python main.py "分析这段文本的情感倾向"

# 交互模式
python main.py

# 多智能体协作
# 在交互模式中输入: multi:研究人工智能在教育领域的应用
```

## 📁 项目结构

```
aime/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── utils.py             # 工具函数
├── planner.py           # 动态规划器
├── factory.py           # Actor工厂
├── actor.py             # 动态Actor
├── progress.py          # 进度管理
├── test_cases.py        # 测试用例
├── requirements.txt     # 依赖列表
├── env.template         # 环境变量模板
└── README.md           # 项目说明
```

## 🎯 使用示例

### 单智能体任务

```python
from main import AimeSystem

aime = AimeSystem()

# 数学计算
result = aime.execute_task("计算 123 + 456 的结果")

# 文本分析
result = aime.execute_task("分析这段文本的情感倾向：今天天气真好！")

# 信息处理
result = aime.execute_task("总结人工智能的发展历程")
```

### 多智能体协作

```python
# 复杂研究任务
result = aime.execute_multi_agent_task(
    "研究机器学习在医疗领域的应用，分析其优势和挑战"
)

# 系统会自动：
# 1. 分解为多个子任务
# 2. 创建专用智能体团队
# 3. 协调执行并整合结果
```

### 交互模式命令

- `<任务描述>` - 执行单智能体任务
- `multi:<任务>` - 执行多智能体协作任务  
- `status` - 查看系统状态
- `help` - 显示帮助信息
- `quit/exit` - 退出系统

## 🧪 测试验证

系统提供完整的测试套件验证核心功能：

### 测试覆盖

- ✅ 基础组件测试
- ✅ 单智能体任务执行
- ✅ 多智能体协作
- ✅ 动态重规划
- ✅ 错误处理
- ✅ 性能基准

### 运行测试

```bash
# 运行所有测试
python test_cases.py

# 快速验证（推荐开始时使用）
python test_cases.py quick

# 查看测试报告
# 测试完成后会显示详细的成功率和性能指标
```

### 预期结果

- **任务完成率**: 80%+
- **平均响应时间**: <30秒
- **智能体创建时间**: <5秒
- **规划准确性**: 70%+（主观评估）

## 🤖 智能体类型

系统支持三种预定义的智能体类型：

### 📊 分析师 (Analyst)
- **擅长**: 数据分析、计算推理、统计评估
- **工具**: 计算器、数据分析、统计工具
- **适用**: 数学计算、数据处理、量化分析

### ⚙️ 执行者 (Executor)  
- **擅长**: 任务执行、文件操作、系统调用
- **工具**: 文件操作、API调用、格式转换
- **适用**: 具体实施、批量处理、结果生成

### 🔍 研究员 (Researcher)
- **擅长**: 信息搜索、内容总结、知识整理
- **工具**: 搜索引擎、内容总结、知识库
- **适用**: 资料收集、信息整合、报告撰写

## ⚙️ 配置选项

在`.env`文件中可配置：

```bash
# 系统参数
MAX_ITERATIONS=5      # 最大执行迭代次数
MAX_RETRIES=3         # 最大重试次数
TIMEOUT_SECONDS=30    # 超时时间

# 调试选项
DEBUG=false           # 调试模式
VERBOSE=false         # 详细输出

# 文件路径
STATE_FILE=aime_state.json  # 状态文件
LOG_FILE=aime.log          # 日志文件
```

## 🔧 故障排除

### 常见问题

1. **API密钥错误**
   ```bash
   # 检查.env文件中的API密钥是否正确
   cat .env | grep API_KEY
   ```

2. **依赖包缺失**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt
   ```

3. **网络连接问题**
   ```bash
   # 检查网络连接
   python -c "import requests; print(requests.get('https://api.openai.com').status_code)"
   ```

4. **权限问题**
   ```bash
   # 确保有文件写入权限
   touch aime_state.json aime.log
   ```

### 调试技巧

1. **启用调试模式**
   ```bash
   # 在.env中设置
   DEBUG=true
   VERBOSE=true
   ```

2. **查看日志**
   ```bash
   tail -f aime.log
   ```

3. **检查状态文件**
   ```bash
   cat aime_state.json | python -m json.tool
   ```

## 📈 性能优化

### 原型级优化

- **缓存LLM响应**: 避免重复调用
- **并行处理**: 使用asyncio处理多任务
- **超时控制**: 设置合理的执行时间限制
- **资源监控**: 监控内存和API调用次数

### 配置建议

- **开发环境**: MAX_ITERATIONS=5, DEBUG=true
- **测试环境**: MAX_ITERATIONS=3, TIMEOUT_SECONDS=60
- **演示环境**: VERBOSE=true, 较短的超时时间

## 🔮 后续发展

### 短期目标 (1-3个月)
- [ ] 集成更多实用工具
- [ ] 改进智能体协作机制
- [ ] 增强错误处理
- [ ] 开发Web界面

### 中期目标 (3-6个月)
- [ ] 支持更多LLM模型
- [ ] 实现智能体记忆系统
- [ ] 添加插件机制
- [ ] 性能优化

### 长期愿景 (6个月+)
- [ ] 生产级架构迁移
- [ ] 企业级安全和监控
- [ ] 自主学习能力
- [ ] 跨域应用扩展

## 📄 许可证

本项目为开源研究项目，遵循MIT许可证。

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📚 相关资源

- [技术报告](technical_report.md) - 详细的架构设计和实现说明
- [论文原文](https://arxiv.org/abs/2507.11988) - Aime框架的学术论文
- [OpenAI API文档](https://platform.openai.com/docs) - OpenAI API使用指南
- [Anthropic API文档](https://docs.anthropic.com/) - Claude API使用指南

---

**⚡ 开始探索多智能体的无限可能！**