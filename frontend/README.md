# StockAI Frontend

StockAI 前端应用，使用 React + TypeScript + Vite 构建，参照 valuecell 项目的 UI/UX 设计。

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **ECharts** - 图表库（替代 Plotly）
- **React Query** - 数据获取和缓存
- **Sonner** - Toast 通知
- **React Markdown** - Markdown 渲染

## 功能特性

- ✅ 股票代码输入和分析（支持多只股票）
- ✅ 分析结果展示（Markdown 格式）
- ✅ 数据表格展示（历史交易数据）
- ✅ 多股票涨跌幅对比图表（ECharts）
- ✅ 与 LangGraph Agent 对话助手
- ✅ 响应式设计，支持暗色主题

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
# 或
yarn install
# 或
pnpm install
```

### 2. 配置环境变量

创建 `.env` 文件（或使用 `.env.local`）：

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### 3. 启动后端 API 服务器

在项目根目录运行：

```bash
conda activate open_manus
python start_frontend_api.py
```

API 服务器将在 http://localhost:8000 启动

### 4. 启动前端开发服务器

在 `frontend` 目录运行：

```bash
npm run dev
```

前端应用将在 http://localhost:3000 启动

### 5. 构建生产版本

```bash
npm run build
```

构建产物在 `dist` 目录

### 6. 预览生产版本

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口
│   │   ├── stock.ts      # 股票相关 API
│   │   └── chat.ts       # 聊天相关 API
│   ├── app/              # 页面组件
│   │   ├── StockAnalysis.tsx    # 股票分析页面
│   │   └── ChatAssistant.tsx     # 对话助手页面
│   ├── components/       # UI 组件
│   │   ├── ui/           # 基础 UI 组件
│   │   ├── StockChart.tsx        # 股票图表组件
│   │   └── StockDataTable.tsx    # 数据表格组件
│   ├── lib/              # 工具函数
│   │   ├── api-client.ts  # API 客户端
│   │   └── utils.ts       # 通用工具函数
│   ├── types/            # TypeScript 类型定义
│   │   ├── stock.ts       # 股票相关类型
│   │   └── chat.ts        # 聊天相关类型
│   ├── App.tsx           # 主应用组件
│   ├── main.tsx          # 应用入口
│   └── index.css         # 全局样式
├── public/               # 静态资源
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## API 接口

### 股票分析

```typescript
POST /api/stock/analyze
Body: {
  stock_code: string,  // 股票代码，支持多只，用逗号分隔
  interval: "1d" | "1m"  // 时间间隔
}
Response: {
  analysis_text: string,  // Markdown 格式的分析结果
  data_table: StockData[],  // 历史数据表格
  chart_data: {  // 图表数据
    dates: string[],
    stocks: { code: string, returns: number[] }[]
  }
}
```

### 聊天

```typescript
POST /api/chat
Body: {
  message: string,
  history?: ChatMessage[]
}
Response: {
  message: string
}
```

## UI/UX 设计

参照 valuecell 项目的设计风格：

- **现代化卡片布局**：使用 Card 组件展示内容
- **清晰的视觉层次**：使用 Tailwind CSS 的间距和颜色系统
- **响应式设计**：适配不同屏幕尺寸
- **暗色主题支持**：自动检测系统主题偏好
- **流畅的交互**：使用 React Query 进行数据加载和缓存

## 开发说明

### 添加新的 API 接口

1. 在 `src/api/` 目录创建对应的 API 文件
2. 使用 `useQuery` 或 `useMutation` hook
3. 在组件中使用这些 hooks

### 添加新的 UI 组件

1. 在 `src/components/ui/` 目录创建基础组件
2. 在 `src/components/` 目录创建业务组件
3. 使用 Tailwind CSS 进行样式设计

### 样式约定

- 使用 Tailwind CSS 类名
- 支持暗色主题（使用 CSS 变量）
- 响应式设计（使用 `lg:`, `md:` 等前缀）

## 故障排除

### API 请求失败

1. 确保后端 API 服务器正在运行（http://localhost:8000）
2. 检查 `.env` 文件中的 `VITE_API_BASE_URL` 配置
3. 检查浏览器控制台的错误信息

### 图表不显示

1. 检查 ECharts 是否正确安装
2. 检查图表数据格式是否正确
3. 查看浏览器控制台的错误信息

### 类型错误

运行类型检查：

```bash
npm run typecheck
```

## 许可证

与主项目保持一致
