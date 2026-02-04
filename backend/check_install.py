#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查依赖是否安装成功"""
try:
    import fastapi
    import uvicorn
    import sqlalchemy
    import pydantic
    import dateutil
    import aiosqlite
    
    print("=" * 60)
    print("✓ 所有依赖已成功安装！")
    print("=" * 60)
    print(f"FastAPI:     {fastapi.__version__}")
    print(f"Uvicorn:     {uvicorn.__version__}")
    print(f"SQLAlchemy:  {sqlalchemy.__version__}")
    print(f"Pydantic:   {pydantic.__version__}")
    print(f"Dateutil:    {dateutil.__version__}")
    print(f"Aiosqlite:   {aiosqlite.__version__}")
    print("=" * 60)
except ImportError as e:
    print(f"FAILED: Dependencies not fully installed, missing: {e}")
    print("\nPlease run: python install_deps.py")
