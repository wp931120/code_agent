# Code Agent

一个基于 OpenAI API 的智能代码助手，能够通过工具调用来帮助用户完成各种编程任务。

## 功能特性

- 🤖 **智能对话**: 基于 OpenAI GPT 模型的自然语言交互
- 🛠️ **工具集成**: 支持文件操作、代码执行、数据可视化等多种工具
- 📊 **数据可视化**: 内置 ECharts 可视化工具，支持多种图表类型
- 🌐 **Web 界面**: 现代化的前端界面，支持实时对话
- 🔧 **可扩展**: 模块化设计，易于添加新工具和功能

## 项目结构

```
code_agent/
├── agent.py           # 核心 Agent 类
├── app.py            # Flask Web 应用
├── config.py         # 配置文件
├── prompt.py         # 系统提示词
├── tools.py          # 工具定义和执行
├── requirements.txt  # Python 依赖
├── frontend/         # 前端文件
│   ├── index.html   # 主页面
│   ├── app.js       # JavaScript 逻辑
│   └── styles.css   # 样式文件
└── workspace/        # 工作空间目录
```

## 安装和使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API

在 `config.py` 中配置你的 OpenAI API 信息：

```python
class Config:
    API_KEY = "your-api-key"
    API_BASE_URL = "your-api-base-url"
    MODEL_NAME = "your-model-name"
```

### 3. 启动应用

```bash
python app.py
```

然后在浏览器中访问 `http://localhost:5000`

## 可用工具

- **write_file**: 写入文件
- **read_file**: 读取文件
- **list_files**: 列出目录文件
- **execute_code**: 执行 Python 代码
- **create_echarts_visualization**: 创建数据可视化图表
- **final_answer**: 提供最终答案

## 技术栈

- **后端**: Python, Flask, OpenAI API
- **前端**: HTML, CSS, JavaScript
- **可视化**: ECharts
- **AI 模型**: OpenAI GPT 系列

## 特性亮点

### 工具系统优化

- 标准化的工具定义结构
- 自动参数验证
- 一致性检查机制
- 降级处理确保系统稳定性

### 前端体验

- 实时流式对话
- 支持换行符正确显示
- 现代化 UI 设计
- 响应式布局

## 开发说明

项目采用模块化设计，各组件职责清晰：

- `agent.py`: 负责与 AI 模型交互和任务执行
- `tools.py`: 定义和管理所有可用工具
- `app.py`: 提供 Web API 接口
- `frontend/`: 用户交互界面

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！