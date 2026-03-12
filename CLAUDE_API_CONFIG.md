# Claude API 集成配置指南

## 配置信息

根据您提供的信息，已完成 Claude API 的集成配置：

### API 配置详情

- **API 端点**: `https://api.chataiapi.com/v1`
- **API Key**: `sk-YAoPKK7Fb1ztVdeQjDgou3hPyMHxEahiicUid40ruc96F8y3`
- **推荐模型**: `claude-sonnet-4-6` (最新的 Claude Sonnet 4.6 版本)

### 可用的 Claude 模型列表

该 API 代理支持以下 Claude 模型：

#### Claude Sonnet 系列（推荐用于生产环境）
- `claude-sonnet-4-6` ⭐ **推荐** - 最新版本，平衡性能和成本
- `claude-sonnet-4-6-thinking` - 带思维链的版本
- `claude-sonnet-4-5-20250929` - 稳定版本
- `claude-sonnet-4-5-20250929-thinking`
- `claude-sonnet-4-20250514`
- `claude-sonnet-4-20250514-thinking`

#### Claude Opus 系列（最强性能）
- `claude-opus-4-6` - 最新最强版本，适合复杂任务
- `claude-opus-4-6-thinking`
- `claude-opus-4-5-20251101`
- `claude-opus-4-5-20251101-thinking`
- `claude-opus-4-1-20250805`
- `claude-opus-4-1-20250805-thinking`
- `claude-opus-4-20250514`
- `claude-opus-4-20250514-thinking`

#### Claude Haiku 系列（快速响应）
- `claude-haiku-4-5-20251001` - 最快速响应，适合简单任务
- `claude-haiku-4-5-20251001-thinking`

## 配置文件修改

### 1. 后端配置文件

文件位置: `backend/app/config.py`

已更新的配置：

```python
# OpenAI 配置（兼容 Claude API）
OPENAI_API_KEY: Optional[str] = (
    os.environ.get("OPENAI_API_KEY", "").strip() or 
    "sk-YAoPKK7Fb1ztVdeQjDgou3hPyMHxEahiicUid40ruc96F8y3"
)
OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "claude-sonnet-4-6").strip()
OPENAI_BASE_URL: Optional[str] = os.environ.get("OPENAI_BASE_URL", "").strip() or "https://api.chataiapi.com/v1"
```

### 2. 使用环境变量（推荐用于生产环境）

创建 `.env` 文件：

```env
OPENAI_API_KEY=sk-YAoPKK7Fb1ztVdeQjDgou3hPyMHxEahiicUid40ruc96F8y3
OPENAI_BASE_URL=https://api.chataiapi.com/v1
OPENAI_MODEL=claude-sonnet-4-6
```

## 使用方式

### 1. 基本对话示例

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-YAoPKK7Fb1ztVdeQjDgou3hPyMHxEahiicUid40ruc96F8y3",
    base_url="https://api.chataiapi.com/v1"
)

response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[
        {"role": "user", "content": "你好，请介绍你自己"}
    ]
)

print(response.choices[0].message.content)
```

### 2. Function Calling 示例

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "find_delayed_orders",
            "description": "查询延误订单",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[
        {"role": "user", "content": "查询延误的订单"}
    ],
    tools=tools,
    tool_choice="auto"
)
```

### 3. 在 APS 系统中使用

系统的 LLM 服务已自动配置，无需额外修改。聊天机器人功能会自动使用 Claude API。

访问路径：
- API 端点: `POST /api/chatbot/chat`
- 前端界面: 已集成在系统中

## 测试脚本

提供了以下测试脚本来验证配置：

1. **list_models.py** - 列出所有可用模型
   ```bash
   cd backend
   python list_models.py
   ```

2. **test_claude_complete.py** - 完整功能测试
   ```bash
   cd backend
   python test_claude_complete.py
   ```

## 注意事项

### ⚠️ API 余额

当前提供的 API Key 余额为 $0，需要充值后才能正常使用。错误信息：

```
用户额度不足, 剩余额度: $0.000000
```

### 解决方案

1. 登录 API 提供商平台充值
2. 或使用新的 API Key 替换配置文件中的密钥

### 🔒 安全建议

1. **不要将 API Key 提交到代码仓库**
   - 添加到 `.gitignore`: `.env`
   - 使用环境变量管理敏感信息

2. **生产环境配置**
   - 使用环境变量而非硬编码
   - 定期轮换 API Key
   - 监控 API 使用量和成本

## 模型选择建议

| 使用场景 | 推荐模型 | 说明 |
|---------|---------|------|
| 生产环境日常对话 | `claude-sonnet-4-6` | 平衡性能和成本，响应质量高 |
| 复杂任务、代码生成 | `claude-opus-4-6` | 最强推理能力，适合复杂问题 |
| 快速响应、简单任务 | `claude-haiku-4-5-20251001` | 响应快，成本低 |
| 需要思维过程 | 带 `-thinking` 后缀的模型 | 显示推理过程，便于调试 |

## 成本优化建议

1. **根据任务选择合适的模型**
   - 简单查询使用 Haiku
   - 复杂分析使用 Sonnet
   - 关键决策使用 Opus

2. **控制 token 使用**
   ```python
   response = client.chat.completions.create(
       model="claude-sonnet-4-6",
       messages=messages,
       max_tokens=500,  # 限制输出长度
   )
   ```

3. **优化对话历史**
   - 限制保留的消息数量（当前配置：20条）
   - 定期清理过期会话（当前配置：30分钟）

## 技术支持

如遇到问题，请检查：

1. API Key 是否有效且有余额
2. 网络连接是否正常
3. API 端点地址是否正确
4. 模型名称是否在支持列表中

## 配置完成清单

- ✅ API 端点配置完成
- ✅ API Key 配置完成  
- ✅ 模型选择配置完成
- ✅ 后端服务集成完成
- ✅ 测试脚本准备完成
- ⚠️ **需要充值 API 余额后才能使用**

---

**配置日期**: 2026-03-11  
**配置人**: AI Assistant  
**系统**: APS (高级计划排程系统)
