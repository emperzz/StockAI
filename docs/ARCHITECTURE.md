# 🏗️ StockAI 前端架构图

## 系统架构

```mermaid
graph TB
    subgraph "用户界面层"
        A[用户浏览器] --> B[Gradio Web界面]
        B --> C[股票代码输入]
        B --> D[分析结果展示]
        B --> E[K线图显示]
    end
    
    subgraph "应用逻辑层"
        F[gradio_app.py] --> G[analyze_stock函数]
        G --> H[get_stock_info函数]
        G --> I[get_stock_data函数]
        G --> J[create_stock_chart函数]
    end
    
    subgraph "数据获取层"
        K[AKShare API] --> L[股票基本信息]
        K --> M[历史交易数据]
        K --> N[实时价格数据]
    end
    
    subgraph "可视化层"
        O[Plotly图表库] --> P[K线图生成]
        O --> Q[交互式图表]
    end
    
    subgraph "数据存储层"
        R[Pandas DataFrame] --> S[数据格式化]
        R --> T[统计分析]
    end
    
    %% 连接关系
    C --> G
    H --> K
    I --> K
    J --> O
    L --> R
    M --> R
    N --> R
    P --> E
    S --> D
    T --> D
    
    %% 样式
    classDef userLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef appLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef dataLayer fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef vizLayer fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef storageLayer fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class A,B,C,D,E userLayer
    class F,G,H,I,J appLayer
    class K,L,M,N dataLayer
    class O,P,Q vizLayer
    class R,S,T storageLayer
```

## 数据流程图

```mermaid
sequenceDiagram
    participant U as 用户
    participant G as Gradio界面
    participant A as 分析模块
    participant AK as AKShare API
    participant P as Plotly图表
    participant D as 数据展示
    
    U->>G: 输入股票代码
    G->>A: 调用analyze_stock()
    A->>AK: 获取股票基本信息
    AK-->>A: 返回基本信息
    A->>AK: 获取历史数据
    AK-->>A: 返回历史数据
    A->>A: 计算统计数据
    A->>P: 创建K线图
    P-->>A: 返回图表对象
    A->>D: 格式化分析结果
    A-->>G: 返回(结果,数据,图表)
    G->>D: 显示分析结果
    G->>D: 显示数据表格
    G->>D: 显示K线图
    D-->>U: 展示完整分析
```

## 模块依赖关系

```mermaid
graph LR
    subgraph "核心模块"
        A[gradio_app.py]
        B[akshare_client.py]
        C[analysis_tools.py]
    end
    
    subgraph "外部依赖"
        D[Gradio]
        E[AKShare]
        F[Plotly]
        G[Pandas]
    end
    
    subgraph "数据流"
        H[股票代码输入]
        I[数据获取]
        J[数据处理]
        K[图表生成]
        L[结果展示]
    end
    
    A --> D
    A --> F
    A --> G
    B --> E
    C --> G
    
    H --> I
    I --> J
    J --> K
    K --> L
    
    A -.-> B
    A -.-> C
```

## 技术栈说明

### 前端技术
- **Gradio 5.44.1**: 现代化Web界面框架
- **Plotly 6.3.0**: 交互式图表库
- **响应式CSS**: 适配不同设备

### 数据处理
- **Pandas 2.2.3**: 数据分析和处理
- **NumPy 2.2.5**: 数值计算
- **AKShare 1.16.84**: 中国股市数据API

### 开发环境
- **Python 3.12**: 运行环境
- **Conda**: 环境管理
- **open_manus**: 项目环境

## 性能优化

### 数据缓存
- 股票基本信息缓存
- 历史数据本地存储
- 图表对象复用

### 异步处理
- 非阻塞数据获取
- 后台数据处理
- 实时更新机制

### 用户体验
- 加载状态提示
- 错误处理机制
- 快速测试功能
