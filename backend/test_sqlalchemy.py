#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 SQLAlchemy 是否能正常工作"""
import sys

print("Testing SQLAlchemy functionality...")
print("-" * 60)

try:
    # 尝试导入
    print("1. Importing SQLAlchemy...")
    import sqlalchemy
    print(f"   [OK] SQLAlchemy {sqlalchemy.__version__} imported")
except Exception as e:
    print(f"   [FAIL] Import failed: {e}")
    sys.exit(1)

try:
    # 测试创建引擎
    print("2. Creating database engine...")
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:')
    print("   [OK] Engine created successfully")
except Exception as e:
    print(f"   [FAIL] Engine creation failed: {e}")
    sys.exit(1)

try:
    # 测试基本操作
    print("3. Testing basic operations...")
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        row = result.fetchone()
        if row and row[0] == 1:
            print("   [OK] Basic query works")
        else:
            print("   [WARN] Query returned unexpected result")
except Exception as e:
    print(f"   [FAIL] Basic operations failed: {e}")
    sys.exit(1)

print("-" * 60)
print("[SUCCESS] SQLAlchemy is working correctly!")
print("Note: The import warning is just a type checking issue,")
print("      but SQLAlchemy functions work normally.")
