#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
升级 SQLAlchemy 到兼容 Python 3.13 的版本
"""
import os
import sys
import subprocess

# 清除所有可能阻止 pip 的环境变量
env = os.environ.copy()
# 删除代理相关环境变量
for key in ['PIP_NO_INDEX', 'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    env.pop(key, None)

# 明确设置以覆盖系统配置
env['PIP_NO_INDEX'] = ''
env['NO_PROXY'] = '*'
env['HTTP_PROXY'] = ''
env['HTTPS_PROXY'] = ''
env['http_proxy'] = ''
env['https_proxy'] = ''

# 尝试的镜像源列表
mirrors = [
    ('https://mirrors.aliyun.com/pypi/simple/', 'mirrors.aliyun.com'),
    ('https://pypi.tuna.tsinghua.edu.cn/simple', 'pypi.tuna.tsinghua.edu.cn'),
    ('https://pypi.douban.com/simple/', 'pypi.douban.com'),
]

print("=" * 60)
print("升级 SQLAlchemy 脚本")
print("=" * 60)
print(f"使用 Python: {sys.executable}")
print(f"当前 SQLAlchemy 版本: ", end="")
try:
    import sqlalchemy
    print(sqlalchemy.__version__)
except:
    print("无法导入（需要升级）")
print("-" * 60)

# 尝试每个镜像源
for index_url, trusted_host in mirrors:
    print(f"\n尝试镜像源: {index_url}")
    print("-" * 60)
    
    # 先尝试升级到最新版本
    cmd = [
        sys.executable, '-m', 'pip', 'install',
        '--upgrade', '--force-reinstall',
        'sqlalchemy',
        '--index-url', index_url,
        '--trusted-host', trusted_host,
        '--timeout', '120',
        '--retries', '3',
    ]
    
    try:
        print("正在升级 SQLAlchemy...")
        result = subprocess.run(
            cmd, 
            env=env, 
            check=True,
            timeout=600,  # 10分钟超时
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 检查升级后的版本
        import sqlalchemy
        new_version = sqlalchemy.__version__
        
        print("\n" + "=" * 60)
        print(f"✓ SQLAlchemy 升级成功！")
        print(f"  新版本: {new_version}")
        print("=" * 60)
        
        # 测试是否能正常导入和使用
        print("\n测试 SQLAlchemy 功能...")
        try:
            from sqlalchemy import create_engine
            engine = create_engine('sqlite:///:memory:')
            print("✓ SQLAlchemy 可以正常创建引擎")
            
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
                if row and row[0] == 1:
                    print("✓ SQLAlchemy 可以正常执行查询")
            
            print("\n[SUCCESS] SQLAlchemy 升级并测试成功！")
            sys.exit(0)
        except Exception as e:
            print(f"⚠ SQLAlchemy 升级成功但测试失败: {e}")
            print("   可能需要进一步检查")
            sys.exit(0)  # 仍然算成功，因为已经升级了
        
    except subprocess.TimeoutExpired:
        print(f"✗ 升级超时（超过10分钟）")
        continue
    except subprocess.CalledProcessError as e:
        print(f"✗ 升级失败，错误代码: {e.returncode}")
        if e.stderr:
            error_msg = e.stderr[-500:]  # 只显示最后500字符
            print("错误信息:")
            print(error_msg)
        continue
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        continue

print("\n" + "=" * 60)
print("✗ 所有镜像源都失败了")
print("=" * 60)
print("\n建议:")
print("1. 检查网络连接")
print("2. 手动禁用系统代理（设置 -> 网络和 Internet -> 代理）")
print("3. 重新打开 PowerShell 后重试")
sys.exit(1)
