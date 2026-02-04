#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证依赖安装并检查版本兼容性"""
import sys

print("=" * 60)
print("后端依赖安装验证")
print("=" * 60)

dependencies = {
    'fastapi': '0.109.0',
    'uvicorn': '0.27.0',
    'sqlalchemy': '2.0.25',
    'pydantic': '2.5.3',
    'python-dateutil': '2.8.2',
    'aiosqlite': '0.19.0'
}

installed = {}
missing = []
version_mismatch = []

# 检查每个依赖
for module_name, required_version in dependencies.items():
    try:
        if module_name == 'python-dateutil':
            import dateutil
            installed[module_name] = dateutil.__version__
        else:
            module = __import__(module_name)
            installed[module_name] = module.__version__
        
        # 检查版本（允许小版本更新）
        installed_ver = installed[module_name]
        req_major, req_minor = required_version.split('.')[:2]
        inst_major, inst_minor = installed_ver.split('.')[:2]
        
        if req_major != inst_major or (req_major == inst_major and req_minor > inst_minor):
            version_mismatch.append((module_name, required_version, installed_ver))
        
    except ImportError:
        missing.append(module_name)
    except Exception as e:
        print(f"检查 {module_name} 时出错: {e}")

# 输出结果
print("\n已安装的依赖:")
print("-" * 60)
for name, version in installed.items():
    status = "[OK]"
    if any(m[0] == name for m in version_mismatch):
        status = "[WARN]"
    print(f"{status} {name:20s} {version}")

if missing:
    print("\n缺失的依赖:")
    print("-" * 60)
    for name in missing:
        print(f"[MISSING] {name}")

if version_mismatch:
    print("\n版本不匹配:")
    print("-" * 60)
    for name, required, installed_ver in version_mismatch:
        print(f"[WARN] {name}: required {required}, installed {installed_ver}")

# 测试导入
print("\n导入测试:")
print("-" * 60)
try:
    import fastapi
    print("[OK] FastAPI can be imported")
except Exception as e:
    print(f"[FAIL] FastAPI import failed: {e}")

try:
    import uvicorn
    print("[OK] Uvicorn can be imported")
except Exception as e:
    print(f"[FAIL] Uvicorn import failed: {e}")

try:
    import sqlalchemy
    print("[OK] SQLAlchemy can be imported")
except Exception as e:
    print(f"[FAIL] SQLAlchemy import failed: {e}")
    print("  Note: SQLAlchemy 2.0.25 may have compatibility issues with Python 3.13")
    print("  Suggestion: Upgrade to SQLAlchemy 2.0.36+ or use Python 3.12")

try:
    import pydantic
    print("[OK] Pydantic can be imported")
except Exception as e:
    print(f"[FAIL] Pydantic import failed: {e}")

try:
    import dateutil
    print("[OK] python-dateutil can be imported")
except Exception as e:
    print(f"[FAIL] python-dateutil import failed: {e}")

try:
    import aiosqlite
    print("[OK] aiosqlite can be imported")
except Exception as e:
    print(f"[FAIL] aiosqlite import failed: {e}")

# 总结
print("\n" + "=" * 60)
if not missing:
    if version_mismatch:
        print("[WARN] All dependencies installed, but some versions don't match")
        print("       This usually doesn't affect usage, but check compatibility")
    else:
        print("[SUCCESS] All dependencies installed successfully!")
else:
    print("[FAIL] Some dependencies are missing, please run install script")
print("=" * 60)
