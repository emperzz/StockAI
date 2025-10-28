# 会话持久化功能使用指南

## 概述

本功能为StockAI项目添加了会话过程和结果的数据保存能力，既能在LangGraph Studio中正常工作，又能在本地持久化会话数据。

## 核心特性

- ✅ **LangGraph Studio兼容**: 不直接使用LangGraph的checkpointer/store，避免Studio报错
- ✅ **本地数据持久化**: 使用SQLite数据库保存会话数据
- ✅ **完整会话记录**: 保存用户输入、AI回复、任务执行结果
- ✅ **任务状态跟踪**: 记录每个任务的执行状态和结果
- ✅ **会话历史查询**: 支持查询历史会话和任务结果

## 数据库结构

### 会话表 (sessions)
- `id`: 会话唯一标识
- `user_id`: 用户ID（可选）
- `title`: 会话标题
- `status`: 会话状态（active, completed, failed）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 消息表 (messages)
- `id`: 消息唯一标识
- `session_id`: 所属会话ID
- `role`: 消息角色（user, assistant, system）
- `content`: 消息内容
- `timestamp`: 消息时间
- `message_type`: 消息类型（text, image, file）

### 任务结果表 (task_results)
- `id`: 任务唯一标识
- `session_id`: 所属会话ID
- `step_id`: 步骤ID
- `step_description`: 步骤描述
- `target_node`: 目标节点
- `result`: 执行结果
- `status`: 状态（pending, running, completed, failed）
- `error_message`: 错误信息
- `created_at`: 创建时间
- `completed_at`: 完成时间

## 使用方法

### 1. 初始化数据库

```bash
# 激活环境
conda activate open_manus

# 初始化数据库
python init_database.py --init

# 检查数据库状态
python init_database.py --status
```

### 2. 查询会话数据

```bash
# 列出最近10个会话
python query_sessions.py --list 10

# 显示指定会话详情
python query_sessions.py --show <SESSION_ID>

# 搜索会话
python query_sessions.py --search "股票分析"
```

### 3. 在代码中使用

```python
from stockai.session_manager import session_manager

# 创建会话
session_id = session_manager.create_session(title="我的股票分析")

# 保存消息
session_manager.save_message(session_id, "user", "请分析一下今天的股市")
session_manager.save_message(session_id, "assistant", "好的，我来为您分析...")

# 保存任务结果
session_manager.save_task_result(
    session_id=session_id,
    step_id="step1",
    step_description="获取市场数据",
    target_node="market_news",
    result="成功获取今日市场数据",
    status="completed"
)

# 查询会话历史
messages = session_manager.get_session_messages(session_id)
tasks = session_manager.get_session_tasks(session_id)
```

## 技术实现

### 1. 数据持久化策略

- **不依赖LangGraph的checkpointer/store**: 避免LangGraph Studio报错
- **节点内部持久化**: 在关键节点中调用持久化功能
- **使用现有SQLite**: 利用项目已有的数据库配置

### 2. 关键修改点

#### AgentState状态扩展
```python
class AgentState(TypedDict):
    # ... 现有字段
    session_id: Optional[str]  # 新增会话ID字段
```

#### 节点集成持久化
- `coordinator_node`: 创建会话，保存用户输入和AI回复
- `planner`: 保存任务规划结果
- `summary`: 保存最终报告，更新会话状态
- 业务节点: 通过`execute_node_with_error_handling`自动保存任务结果

#### 工具函数
- `get_or_create_session()`: 获取或创建会话
- `save_message_to_db()`: 保存消息到数据库
- `save_task_result_to_db()`: 保存任务结果到数据库

## 配置说明

### 数据库配置
使用`config.py`中的现有SQLite配置：
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///summa.db'
```

### 环境变量
无需额外环境变量，使用现有配置即可。

## 故障排除

### 1. 数据库初始化失败
```bash
# 检查数据库文件权限
ls -la summa.db

# 重新初始化
rm summa.db
python init_database.py --init
```

### 2. 会话查询失败
```bash
# 检查数据库状态
python init_database.py --status

# 查看详细错误信息
python query_sessions.py --list 1
```

### 3. LangGraph Studio报错
确保没有在`graph.compile()`中配置checkpointer或store：
```python
# ✅ 正确 - 不配置持久化
graph = create_graph().compile()

# ❌ 错误 - 会导致Studio报错
graph = create_graph().compile(checkpointer=..., store=...)
```

## 性能考虑

- **数据库连接**: 使用连接池管理数据库连接
- **批量操作**: 支持批量保存消息和任务结果
- **索引优化**: 在session_id和timestamp字段上建立索引
- **数据清理**: 可定期清理过期会话数据

## 扩展功能

### 1. 会话导出
```python
# 导出会话为JSON
def export_session(session_id):
    session_info = session_manager.get_session(session_id)
    messages = session_manager.get_session_messages(session_id)
    tasks = session_manager.get_session_tasks(session_id)
    
    return {
        'session': session_info,
        'messages': messages,
        'tasks': tasks
    }
```

### 2. 会话统计
```python
# 获取会话统计信息
def get_session_stats():
    # 实现会话统计逻辑
    pass
```

### 3. 数据备份
```python
# 备份数据库
def backup_database():
    # 实现数据库备份逻辑
    pass
```

## 注意事项

1. **数据安全**: 会话数据包含用户输入，注意数据安全
2. **存储空间**: 长期使用可能产生大量数据，考虑定期清理
3. **性能影响**: 每次消息和任务都会写入数据库，可能影响性能
4. **错误处理**: 持久化失败不应影响主要功能，已添加异常处理

## 更新日志

- **v1.0.0**: 初始版本，支持基础会话持久化
- 支持会话创建、消息保存、任务结果保存
- 支持会话历史查询和管理
- 兼容LangGraph Studio使用
