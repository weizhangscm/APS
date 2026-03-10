# AI Pilot LLM 集成 - 使用说明

## 概述

AI Pilot 现已升级为真正的 LLM 驱动的智能助手，使用 OpenAI GPT 模型提供自然语言对话能力，并通过 Function Calling 执行排程系统操作。

## 主要特性

✅ **智能对话**：基于 OpenAI GPT-4o 的自然语言理解
✅ **多轮对话**：支持上下文记忆的连续对话
✅ **Function Calling**：智能识别用户意图并自动调用相应功能
✅ **排程操作**：查询延误订单、运行启发式排程、取消/保存计划

## 环境配置

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 设置环境变量

在运行后端服务前，需要设置 OpenAI API 密钥：

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
$env:OPENAI_MODEL="gpt-4o"  # 可选，默认为 gpt-4o
```

**Windows (命令提示符):**
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
set OPENAI_MODEL=gpt-4o
```

**Linux/macOS:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
export OPENAI_MODEL="gpt-4o"  # 可选
export OPENAI_BASE_URL=""      # 可选，自定义 API 端点
```

### 3. 永久配置（可选）

创建 `.env` 文件或将环境变量添加到系统环境变量中。

## 架构说明

```
用户 → ChatBot.vue → FastAPI → LLM Service → OpenAI API
                                     ↓
                              Function Calling
                                     ↓
                              Agent Proxy → Scheduling Engine
```

### 核心模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 配置管理 | `backend/app/config.py` | 管理 OpenAI API 配置和环境变量 |
| LLM 服务 | `backend/app/services/llm_service.py` | OpenAI API 调用、对话管理、Function Calling |
| 动作执行器 | `backend/app/services/agent_proxy.py` | 执行排程引擎操作 |
| API 路由 | `backend/app/routers/chatbot.py` | 聊天 API 端点 |

## 可用功能

AI Pilot 现在支持以下功能：

### 1. 查询延误订单
```
用户: "有哪些延误的订单？"
用户: "Show me delayed orders"
```

### 2. 运行启发式排程
```
用户: "运行启发式排程，显示区间 3.15-3.25，资源选择 装配工位-1"
用户: "Run heuristic scheduling for Assembly Station-1, display range 3.15 to 3.25"
```

### 3. 取消计划
```
用户: "取消当前排程计划"
用户: "Cancel the current plan"
```

### 4. 保存计划
```
用户: "保存排程计划"
用户: "Save the scheduling plan"
```

### 5. 自由对话
```
用户: "什么是启发式排程？"
用户: "How does the APS system work?"
```

## Function Calling 工具

LLM 可以自动调用以下工具：

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `find_delayed_orders` | 查询延误订单 | 无 |
| `run_heuristic` | 运行启发式排程 | `display_start_date`, `display_end_date`, `resource_names`, `expected_date_value`, `order_internal_relation` |
| `cancel_plan` | 取消计划 | `resource_ids`, `product_ids` |
| `save_plan` | 保存计划 | `resource_ids`, `product_ids` |

## 对话管理

### 会话存储
- 使用内存缓存存储会话历史
- 每个会话保留最近 20 条消息（可配置）
- 30 分钟无活动自动清理过期会话

### 多轮对话
前端可以传递 `conversation_id` 来维持对话上下文：

```javascript
// 第一次对话
const response1 = await api.post('/chatbot/chat', {
  message: '有延误订单吗？',
  conversation_id: 'user-session-123'
});

// 第二次对话（保持上下文）
const response2 = await api.post('/chatbot/chat', {
  message: '运行启发式排程处理这些订单',
  conversation_id: 'user-session-123'  // 相同的 ID
});
```

## 配置参数

在 `backend/app/config.py` 中可配置：

```python
# OpenAI 配置
OPENAI_API_KEY: str  # 必需，从环境变量读取
OPENAI_MODEL: str = "gpt-4o"  # 模型名称
OPENAI_BASE_URL: str = None  # 自定义 API 端点

# 对话配置
MAX_CONVERSATION_HISTORY: int = 20  # 最大消息数
CONVERSATION_TIMEOUT_MINUTES: int = 30  # 会话超时
```

## System Prompt

AI Pilot 使用以下系统提示：

```
你是 APS（高级计划排程系统）的 AI 助手。你可以帮助用户：
- 查询延误订单
- 运行启发式排程（需要参数：显示区间、资源、日期等）
- 取消或保存排程计划
- 回答关于排程系统的问题

请用简洁专业的语言与用户交流。
```

可在 `llm_service.py` 中根据需要修改。

## 故障排除

### 问题：系统提示"未设置 OPENAI_API_KEY"
**解决方案**：确保在启动后端服务前设置了环境变量 `OPENAI_API_KEY`

### 问题：API 调用超时
**解决方案**：
1. 检查网络连接
2. 如果在中国大陆，可能需要设置代理或使用 `OPENAI_BASE_URL` 指向国内中转服务

### 问题：对话上下文丢失
**解决方案**：确保前端在每次请求时传递相同的 `conversation_id`

### 问题：Function Calling 不工作
**解决方案**：
1. 检查 OpenAI 模型是否支持 Function Calling（gpt-4o、gpt-4-turbo 等）
2. 查看后端日志确认工具调用情况

## 成本优化建议

1. **使用更便宜的模型**：如果对话复杂度不高，可以使用 `gpt-3.5-turbo`
2. **限制对话历史**：减少 `MAX_CONVERSATION_HISTORY` 可以降低 token 使用量
3. **缓存常见问题**：为常见问题添加快速响应路径，避免每次都调用 LLM

## 未来增强方向

- [ ] 支持流式响应（Server-Sent Events）
- [ ] 添加更多排程相关工具（资源利用率查询、订单状态更新等）
- [ ] 支持多语言自动检测
- [ ] 集成知识库（RAG）提供更专业的领域知识
- [ ] 添加对话历史持久化（数据库存储）

## API 示例

### 请求格式
```json
POST /api/chatbot/chat
{
  "message": "有哪些延误的订单？",
  "conversation_id": "user-123",
  "context": {
    "locale": "zh-CN"
  }
}
```

### 响应格式
```json
{
  "reply": "已查询到 3 个延误订单：\n1. PO-2024-001 交期 2024-03-15 计划完成 2024-03-18 延误 72 小时\n...",
  "action_result": {
    "success": true,
    "count": 3,
    "orders": [...]
  },
  "action_type": "find_delayed_orders",
  "context_for_next": null
}
```

## 开发者注意事项

### 添加新的工具函数

1. 在 `llm_service.py` 的 `TOOLS` 列表中添加工具定义
2. 在 `agent_proxy.py` 的 `execute_action` 函数中添加对应的执行逻辑
3. 更新本文档和系统提示

### 修改 System Prompt

编辑 `backend/app/services/llm_service.py` 中的 `SYSTEM_PROMPT` 变量。

### 日志调试

查看后端日志了解 LLM 调用和工具执行详情：
```python
logger.info(f"Executing tool: {function_name} with args: {function_args}")
```

## 许可与致谢

本 AI Pilot 集成基于 OpenAI API 构建，需要有效的 OpenAI API 密钥才能使用。
