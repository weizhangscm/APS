# 登录问题修复指南

## 问题诊断

经过检查，发现以下情况：

✅ **数据库正常** - admin 用户存在，密码哈希正确
✅ **前端代码正常** - Login.vue 配置正确
✅ **后端代码正常** - auth.py 认证逻辑正确
❌ **后端服务未启动** - 这是登录失败的根本原因

## 解决方案

### 1. 启动后端服务

#### 步骤 1：打开终端
在 VS Code 或 Cursor 中打开新终端

#### 步骤 2：进入后端目录
```powershell
cd backend
```

#### 步骤 3：设置环境变量（如果要使用 AI Pilot）
```powershell
.\set_env.ps1
```

或手动设置：
```powershell
$env:OPENAI_API_KEY="sk-B3G5StfWpvvV2w4ScGlbmAI2hR6l0ypvUfA43RBMHBHqPJ7Z"
```

#### 步骤 4：启动服务
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 步骤 5：验证服务运行
你应该看到类似输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
已创建默认管理员账户: admin / admin123
INFO:     Application startup complete.
```

### 2. 启动前端服务

打开另一个终端：

```powershell
cd frontend
npm run dev
```

### 3. 测试登录

1. 打开浏览器访问前端地址（通常是 http://localhost:5173 或 http://localhost:3000）
2. 使用默认账户登录：
   - 用户名：`admin`
   - 密码：`admin123`

## 验证检查清单

- [ ] 后端服务正在运行（端口 8000）
- [ ] 前端服务正在运行（端口 3000 或 5173）
- [ ] 访问 http://localhost:8000/docs 可以看到 API 文档
- [ ] 访问 http://localhost:8000/health 返回 `{"status":"healthy"}`

## 常见问题

### Q1: 端口被占用
**错误信息**: `Address already in use`

**解决方案**:
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000

# 结束进程（替换 PID）
taskkill /PID <进程ID> /F

# 或使用不同端口启动
uvicorn app.main:app --reload --port 8001
```

### Q2: 模块未找到错误
**错误信息**: `ModuleNotFoundError`

**解决方案**:
```powershell
# 确保已安装依赖
pip install -r requirements.txt
```

### Q3: 数据库错误
**错误信息**: `No such table: users`

**解决方案**:
```powershell
# 删除旧数据库并重新初始化
rm aps.db
python -c "from app.database import init_db; init_db()"
```

## 快速启动脚本

为了方便，我创建了启动脚本：

### Windows PowerShell (`start_backend.ps1`)
```powershell
cd backend
$env:OPENAI_API_KEY="sk-B3G5StfWpvvV2w4ScGlbmAI2hR6l0ypvUfA43RBMHBHqPJ7Z"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 使用方法
```powershell
.\start_backend.ps1
```

## 测试登录

运行测试脚本验证：
```powershell
cd backend
python test_api.py
```

成功输出应该显示：
```
[SUCCESS] Login works correctly!
```

---

## 下一步

1. **启动后端**: `cd backend && uvicorn app.main:app --reload`
2. **启动前端**: `cd frontend && npm run dev`  
3. **访问登录页**: 浏览器打开前端地址
4. **登录**: 使用 admin / admin123

如果还有问题，请查看终端的错误日志。
