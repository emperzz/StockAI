# StockAI - 中国股市 AI 分析项目

## 项目简介

StockAI 基于 LangGraph 与 LangChain 构建后端智能体，使用 AKShare 获取中国股市数据，前端采用 Gradio 展示分析结果，并支持用 LangGraph Studio 在浏览器中调试与评测智能体流程。

## 技术栈

- **后端核心**: LangChain + LangGraph
- **测试/可视化**: LangGraph Studio（基于 `langgraph-cli`）
- **前端界面**: Gradio
- **数据源**: AKShare

## 项目结构（关键文件）

```
StockAI/
├── langgraph.json                 # LangGraph Studio 图配置（graph id: my_agent）
├── config.py                      # 项目配置（参考 config_example.py）
├── config.toml                    # 其他可选配置
├── start_frontend.py              # 启动 Gradio 前端
├── stockai/
│   ├── agent.py                   # LangGraph 图定义（导出变量：graph）
│   ├── state.py                   # 状态定义
│   ├── llm.py                     # LLM 封装
│   ├── frontend/
│   │   └── gradio_app.py          # Gradio 应用
│   ├── tools/                     # 工具与数据接入
│   └── requirements.txt           # Python 依赖
└── README.md
```

## 环境与依赖

1) 激活项目环境（Windows/PowerShell 示例）
```bash
conda activate your_env
```

2) 安装依赖
```bash
pip install -r stockai/requirements.txt
# 如需本地调试 Studio，建议确保安装 CLI：
pip install -U langgraph-cli
```

3) 配置参数
- 若需自定义配置，参考 `config_example.py` 并在 `config.py` 中填写。
- 如需使用 `.env`，可在项目根目录创建 `.env`，与 `langgraph.json` 中的 `env` 对应（可选）。

## 使用 LangGraph Studio 启动与调试

项目已提供 `langgraph.json`：

```json
{
  "dependencies": ["."],
  "graphs": {
    "my_agent": "./stockai/agent.py:graph"
  },
  "env": ".env"
}
```

启动步骤：
1) 激活环境并安装依赖（见上）
2) 在项目根目录运行 Studio 开发服务
```bash
langgraph dev --host 0.0.0.0 --port 2024
```
3) 打开浏览器访问 `http://localhost:2024`
4) 在左侧选择图 `my_agent`，创建/选择会话，输入自然语言指令进行交互

常见问题：
- 如提示未找到 CLI，先执行 `pip install -U langgraph-cli`。
- 如果变更了图导出变量名或路径，请同步更新 `langgraph.json` 中的 `graphs` 配置。

### 典型输入示例
- “今天大盘表现如何？给出新闻要点与板块异动。”
- “帮我从新能源车相关板块里找出龙头股，并解释理由。”
- “根据最近一周走势，分析 600036 的量价关系与风险点。”

## 启动 Gradio 前端

```bash
conda activate your_env
python start_frontend.py
```

启动后访问 `http://localhost:7860`。

## 功能特性

- 实时股市数据获取（AKShare）
- AI 智能分析与规划（LangGraph Planner）
- 趋势与量价关系分析、龙头股/相似度分析
- Gradio 前端可视化

## 开发说明

- 尽量保持模块化，最小化修改面；图定义位于 `stockai/agent.py`，状态定义位于 `stockai/state.py`。
- 如需在 Studio 中新增节点或边，请在 `agent.py` 中编辑后重启 `langgraph dev`。
