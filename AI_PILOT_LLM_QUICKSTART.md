# AI Pilot LLM - 快速开始指南

## 🚀 快速启动

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量
**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

**Linux/macOS:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### 3. 启动服务
```bash
cd backend
uvicorn app.main:app --reload
```

### 4. 打开前端
访问前端应用，点击右下角的 "AI Pilot" 浮动按钮。

## 💬 使用示例

### 示例 1：查询延误订单
```
你: "有哪些延误的订单？"
AI: "已查询到 3 个延误订单：
     1. PO-2024-001 交期 2024-03-15 ...
     ..."
```

### 示例 2：运行排程
```
你: "运行启发式排程，显示区间 3.15-3.25，资源选择 装配工位-1"
AI: "启发式排程已完成。已排程 15 个订单，45 个工序。"
```

### 示例 3：多轮对话
```
你: "有延误订单吗？"
AI: "有 3 个延误订单..."

你: "运行启发式处理这些订单"
AI: "启发式排程已完成..."
```

### 示例 4：保存计划
```
你: "保存当前的排程计划"
AI: "计划已保存成功。"
```

## ⚙️ 可选配置

在环境变量中设置（可选）：

```bash
# 使用不同的模型（默认 gpt-4o）
export OPENAI_MODEL="gpt-4-turbo"

# 使用自定义 API 端点（国内中转等）
export OPENAI_BASE_URL="https://your-proxy.com/v1"
```

## 🔧 故障排除

### 问题：提示"未设置 OPENAI_API_KEY"
**解决**：确保在启动后端前设置了环境变量

### 问题：API 调用超时
**解决**：检查网络连接，或设置 `OPENAI_BASE_URL` 使用代理

### 问题：对话上下文丢失
**解决**：不要刷新页面，保持 AI Pilot 抽屉打开状态

## 📚 更多文档

- **完整使用说明**: `AI_PILOT_LLM_README.md`
- **实施总结**: `AI_PILOT_LLM_SUMMARY.md`
- **原始计划**: `AI Pilot LLM.md`

## 🎯 功能特性

✅ 自然语言理解（GPT-4o）
✅ 多轮对话支持
✅ 智能排程操作
✅ 延误订单查询
✅ 计划保存/取消
✅ 中英文支持

## ⚠️ 注意事项

1. 需要有效的 OpenAI API Key
2. API 调用会产生费用
3. 中国大陆可能需要网络代理
4. 会话在30分钟无活动后自动清理

## 🆘 获取帮助

如有问题，请查看详细文档或检查后端日志输出。

---
**版本**: 1.0.0  
**更新日期**: 2026-03-10
