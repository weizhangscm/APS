# Claude API 配置验证清单

## 📋 配置验证步骤

### 第 1 步: 检查配置文件 ✅

```bash
# 检查主配置文件
cat backend/app/config.py
```

期望内容：
- ✅ `OPENAI_API_KEY` = "sk-YAoPKK7Fb1ztVdeQjDgou3hPyMHxEahiicUid40ruc96F8y3"
- ✅ `OPENAI_BASE_URL` = "https://api.chataiapi.com/v1"
- ✅ `OPENAI_MODEL` = "claude-sonnet-4-6"

### 第 2 步: 检查文件完整性 ✅

运行以下命令检查所有文件是否存在：

```bash
# 文档文件
ls CLAUDE_API_CONFIG.md
ls CLAUDE_API_QUICKSTART.md
ls CLAUDE_API_SUMMARY.md
ls CLAUDE_API_CHECKLIST.md

# 测试脚本
ls backend/list_models.py
ls backend/test_claude_api.py
ls backend/test_claude_complete.py
ls backend/claude_examples.py

# 配置文件
ls backend/.env.example
ls backend/app/config.py
```

### 第 3 步: 充值 API 余额 ⚠️

**当前状态**: 余额不足（$0）

**操作步骤**:
1. 访问: https://api.chataiapi.com
2. 登录账户
3. 充值余额
4. 确认余额可用

### 第 4 步: 测试 API 连接 ⏳

充值完成后运行：

```bash
cd backend

# 测试 1: 列出可用模型
python list_models.py

# 测试 2: 完整功能测试
python test_claude_complete.py
```

**期望结果**:
```
[SUCCESS] 所有测试通过！Claude API 配置正确。
推荐使用的模型: claude-sonnet-4-6
```

### 第 5 步: 验证系统集成 ⏳

```bash
# 启动后端
cd backend
python run.py

# 在新终端启动前端
cd frontend
npm run dev
```

**验证项目**:
- [ ] 后端服务启动成功（端口 8000）
- [ ] 前端服务启动成功（端口 3000/5173）
- [ ] 可以访问聊天界面
- [ ] 发送测试消息："你好"
- [ ] 收到 Claude 的回复

### 第 6 步: 测试 Function Calling ⏳

在聊天界面输入：

1. **测试延误订单查询**
   ```
   帮我查询延误的订单
   ```
   期望：系统调用 `find_delayed_orders` 函数

2. **测试排程功能**
   ```
   运行排程算法
   ```
   期望：系统询问排程参数或调用 `run_heuristic` 函数

3. **测试多轮对话**
   ```
   第一轮: 我叫张三
   第二轮: 你还记得我叫什么吗？
   ```
   期望：Claude 能记住用户名字

---

## 🎯 完整性检查清单

### 配置文件
- [x] `backend/app/config.py` - 主配置文件已更新
- [x] `backend/.env.example` - 环境变量模板已创建
- [x] `backend/app/services/llm_service.py` - LLM 服务（已存在）

### 测试工具
- [x] `backend/list_models.py` - 模型列表查询工具
- [x] `backend/test_claude_api.py` - 基础 API 测试
- [x] `backend/test_claude_complete.py` - 完整功能测试

### 示例代码
- [x] `backend/claude_examples.py` - 6个使用示例

### 文档
- [x] `CLAUDE_API_CONFIG.md` - 详细配置文档
- [x] `CLAUDE_API_QUICKSTART.md` - 快速开始指南
- [x] `CLAUDE_API_SUMMARY.md` - 配置总结
- [x] `CLAUDE_API_CHECKLIST.md` - 本验证清单

---

## 🔍 故障排查

### 问题 1: API 连接失败

**症状**: 
```
Error: Failed to connect to API
```

**检查**:
- [ ] 网络连接是否正常
- [ ] API 端点地址是否正确
- [ ] 防火墙是否阻止连接

### 问题 2: 余额不足

**症状**:
```
Error code: 403 - 用户额度不足, 剩余额度: $0.000000
```

**解决**:
- [ ] 访问 API 平台充值
- [ ] 确认充值成功
- [ ] 等待余额更新（可能需要几分钟）

### 问题 3: 模型不可用

**症状**:
```
Error code: 503 - model_not_found
```

**解决**:
- [ ] 运行 `python list_models.py` 查看可用模型
- [ ] 更新配置文件使用可用的模型
- [ ] 重启后端服务

### 问题 4: Function Calling 不工作

**症状**: Claude 直接回答而不调用函数

**检查**:
- [ ] Tools 定义格式是否正确
- [ ] `tool_choice` 参数是否设置为 "auto"
- [ ] 用户消息是否清晰表达了意图

---

## 📊 测试结果记录

### API 连接测试
- 日期: _______________
- 模型列表查询: [ ] 成功 [ ] 失败
- 基础对话测试: [ ] 成功 [ ] 失败
- Function Calling: [ ] 成功 [ ] 失败
- 多轮对话: [ ] 成功 [ ] 失败

### 系统集成测试
- 日期: _______________
- 后端启动: [ ] 成功 [ ] 失败
- 前端启动: [ ] 成功 [ ] 失败
- 聊天功能: [ ] 成功 [ ] 失败
- 订单查询: [ ] 成功 [ ] 失败
- 排程功能: [ ] 成功 [ ] 失败

---

## ✅ 最终确认

配置完成后，确认以下所有项目：

- [ ] API Key 已配置
- [ ] Base URL 已配置
- [ ] Model 已选择
- [ ] 余额已充值（⚠️ 当前待完成）
- [ ] API 连接测试通过
- [ ] Function Calling 工作正常
- [ ] 系统集成测试通过
- [ ] 文档已阅读并理解

---

## 📞 获取帮助

如果遇到问题：

1. **查看文档**
   - CLAUDE_API_CONFIG.md - 详细配置说明
   - CLAUDE_API_QUICKSTART.md - 快速开始

2. **运行测试**
   - `python list_models.py` - 验证 API 连接
   - `python test_claude_complete.py` - 完整测试

3. **查看示例**
   - `claude_examples.py` - 代码示例

---

**配置完成日期**: 2026-03-11  
**下一步**: 充值 API 余额后运行测试  
**预计可用时间**: 充值后立即可用
