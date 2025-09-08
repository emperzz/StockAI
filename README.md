# StockAI - 中国股市AI分析项目

## 项目简介

StockAI是一个基于LangGraph和Gradio的中国股市AI分析项目，通过AKShare获取实时股市数据，使用AI技术进行智能分析和预测。

## 技术栈

- **后端核心**: LangChain + LangGraph
- **前端界面**: Gradio
- **测试平台**: LangGraph Studio
- **数据源**: AKShare（中国股市数据API）

## 项目结构

```
StockAI/
├── my_agent/                     # 主应用目录
│   ├── agent.py                  # LangGraph图定义
│   ├── state.py                  # 状态定义
│   ├── tools/                    # 后端工具模块
│   │   ├── akshare_client.py     # AKShare数据获取
│   │   └── analysis_tools.py     # 分析工具
│   ├── frontend/                 # 前端模块
│   │   └── gradio_app.py         # Gradio应用
│   └── requirements.txt          # 项目依赖
├── langgraph.json                # LangGraph Studio配置
├── .env.example                  # 环境变量示例
└── README.md                     # 项目说明
```

## 安装和运行

1. 克隆项目
2. 安装依赖: `pip install -r my_agent/requirements.txt`
3. 配置环境变量: 复制`.env.example`为`.env`并填入配置
4. 运行项目: 使用LangGraph Studio或直接运行Gradio应用

## 功能特性

- 实时股市数据获取
- AI智能分析
- 技术指标计算
- 可视化图表展示
- 用户友好的交互界面

## 开发说明

本项目遵循模块化设计原则，前后端分离，便于维护和扩展。
