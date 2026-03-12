# Claude API 快速使用指南

## 配置已完成 ✅

您的 APS 系统已成功配置 Claude API！

### 配置摘要

- **API 端点**: https://api.chataiapi.com/v1
- **模型**: claude-sonnet-4-6
- **状态**: 配置完成，等待充值

## ⚠️ 重要提示

**当前 API Key 余额不足，需要充值后才能使用。**

余额不足错误信息：
```
用户额度不足, 剩余额度: $0.000000
```

## 快速测试步骤

### 1. 充值后测试 API 连接

```bash
cd backend
python list_models.py           # 列出所有可用模型
python test_claude_complete.py  # 完整功能测试
```

### 2. 启动 APS 系统

```bash
# 启动后端
cd backend
python run.py

# 启动前端（新终端）
cd frontend
npm run dev
```

### 3. 使用聊天机器人

访问前端界面，在聊天框中输入：
- "你好"
- "查询延误的订单"
- "帮我运行排程"

## 可用模型对比

| 模型 | 性能 | 速度 | 成本 | 适用场景 |
|------|-----|------|------|---------|
| claude-sonnet-4-6 ⭐ | 高 | 快 | 中 | 日常对话、业务查询 |
| claude-opus-4-6 | 最高 | 中 | 高 | 复杂分析、代码生成 |
| claude-haiku-4-5 | 中 | 最快 | 低 | 简单查询、快速响应 |

## 配置文件位置

- **后端配置**: `backend/app/config.py`
- **环境变量模板**: `backend/.env.example`
- **LLM 服务**: `backend/app/services/llm_service.py`

## 更换 API Key

如需更换 API Key，有两种方式：

### 方式 1: 使用环境变量（推荐）

创建 `backend/.env` 文件：
```env
OPENAI_API_KEY=你的新API_KEY
OPENAI_BASE_URL=https://api.chataiapi.com/v1
OPENAI_MODEL=claude-sonnet-4-6
```

### 方式 2: 修改配置文件

编辑 `backend/app/config.py`，替换第 16 行的 API Key。

## 常见问题

### Q1: 如何查看可用模型？
```bash
cd backend
python list_models.py
```

### Q2: 如何测试 API 连接？
```bash
cd backend
python test_claude_complete.py
```

### Q3: 如何切换模型？

修改环境变量 `OPENAI_MODEL` 或直接修改 `config.py` 第 19 行。

推荐模型：
- 生产环境: `claude-sonnet-4-6`
- 测试环境: `claude-haiku-4-5-20251001`
- 高要求任务: `claude-opus-4-6`

### Q4: 余额不足怎么办？

联系 API 提供商（https://api.chataiapi.com）充值。

### Q5: 支持哪些功能？

✅ 基本对话
✅ 中文理解
✅ Function Calling（工具调用）
✅ 多轮对话
✅ 上下文记忆（30分钟）

## 集成的功能

系统已集成以下 AI 功能：

1. **智能对话** - 回答用户问题
2. **订单查询** - 查询延误订单
3. **排程调度** - 运行启发式排程
4. **计划管理** - 保存/取消排程计划

## 技术细节

- **OpenAI SDK 兼容**: 使用标准 OpenAI Python SDK
- **Function Calling**: 支持工具调用
- **会话管理**: 自动保存对话历史
- **超时清理**: 30分钟后自动清理会话

## 文件清单

- ✅ `backend/app/config.py` - 主配置文件
- ✅ `backend/app/services/llm_service.py` - LLM 服务
- ✅ `backend/list_models.py` - 模型列表工具
- ✅ `backend/test_claude_complete.py` - 完整测试脚本
- ✅ `CLAUDE_API_CONFIG.md` - 详细配置文档
- ✅ `CLAUDE_API_QUICKSTART.md` - 本文件

## 下一步

1. ✅ 配置完成
2. ⚠️ **充值 API 余额**
3. ✅ 运行测试脚本验证
4. ✅ 启动系统开始使用

---

**需要帮助？** 查看详细文档: [CLAUDE_API_CONFIG.md](./CLAUDE_API_CONFIG.md)

**配置完成时间**: 2026-03-11
