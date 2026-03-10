# AI Pilot LLM 设置说明

## 🔑 API Key 已配置

您的 OpenAI API Key 已准备就绪：
```
sk-B3G5StfWpvvV2w4ScGlbmAI2hR6l0ypvUfA43RBMHBHqPJ7Z
```

## 🚀 快速启动

### 方法 1：使用 PowerShell 脚本（推荐 - Windows）

```powershell
cd backend
.\set_env.ps1
uvicorn app.main:app --reload
```

### 方法 2：使用 Bash 脚本（Linux/macOS）

```bash
cd backend
source ./set_env.sh
uvicorn app.main:app --reload
```

### 方法 3：手动设置环境变量

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-B3G5StfWpvvV2w4ScGlbmAI2hR6l0ypvUfA43RBMHBHqPJ7Z"
$env:OPENAI_MODEL="gpt-4o"
```

**Windows CMD:**
```cmd
set OPENAI_API_KEY=sk-B3G5StfWpvvV2w4ScGlbmAI2hR6l0ypvUfA43RBMHBHqPJ7Z
set OPENAI_MODEL=gpt-4o
```

**Linux/macOS:**
```bash
export OPENAI_API_KEY="sk-B3G5StfWpvvV2w4ScGlbmAI2hR6l0ypvUfA43RBMHBHqPJ7Z"
export OPENAI_MODEL="gpt-4o"
```

## 📝 完整启动步骤

### 1. 安装依赖（首次使用）

```bash
cd backend
pip install -r requirements.txt
```

### 2. 设置环境变量并启动

```powershell
# Windows PowerShell
cd backend
.\set_env.ps1
uvicorn app.main:app --reload
```

### 3. 访问前端

打开前端应用，点击右下角的 **"AI Pilot"** 按钮即可开始对话！

## 💬 测试对话

启动成功后，在 AI Pilot 中尝试：

1. **查询延误订单**
   ```
   有哪些延误的订单？
   ```

2. **运行排程**
   ```
   运行启发式排程，显示区间 3.15-3.25，资源选择 装配工位-1
   ```

3. **自由对话**
   ```
   什么是启发式排程？
   ```

## 🔧 验证配置

启动后端后，您应该看到类似输出：
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

如果看到错误"未设置 OPENAI_API_KEY"，说明环境变量未正确设置。

## 📂 配置文件说明

| 文件 | 用途 |
|------|------|
| `set_env.ps1` | PowerShell 环境变量设置脚本 |
| `set_env.sh` | Bash 环境变量设置脚本 |
| `.env.example` | 环境变量示例文件 |

## ⚠️ 安全提醒

- ✅ API Key 已包含在设置脚本中
- ⚠️ 请勿将这些文件提交到公共代码仓库
- 💡 建议将 `set_env.ps1`、`set_env.sh`、`.env` 添加到 `.gitignore`

## 🆘 故障排除

### 问题：提示"未设置 OPENAI_API_KEY"
**解决**：
1. 确保在启动 uvicorn 之前运行了设置脚本
2. 在同一个终端窗口中启动服务
3. 验证环境变量：`echo $env:OPENAI_API_KEY`（PowerShell）

### 问题：API 调用失败
**解决**：
1. 检查 API Key 是否有效
2. 确认网络连接正常
3. 查看后端日志获取详细错误信息

## 📚 更多文档

- **快速开始**: `AI_PILOT_LLM_QUICKSTART.md`
- **完整说明**: `AI_PILOT_LLM_README.md`
- **实施总结**: `AI_PILOT_LLM_SUMMARY.md`

---
**准备就绪！** 现在可以启动服务并体验 AI Pilot 的智能对话功能了！ 🚀
