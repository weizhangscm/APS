# -*- coding: utf-8 -*-
"""
测试服务器 - 验证代码是否正确加载
"""
import sys
sys.path.insert(0, '.')

import uvicorn

if __name__ == "__main__":
    print("Starting test server...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
