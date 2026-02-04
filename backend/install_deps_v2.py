#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安装后端依赖的 Python 脚本 V2
尝试多个镜像源，并添加超时和重试机制
"""
import os
import sys
import subprocess
import time

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
print("后端依赖安装脚本 V2")
print("=" * 60)
print(f"使用 Python: {sys.executable}")
print(f"requirements.txt: {os.path.abspath('requirements.txt')}")
print("-" * 60)

# 尝试每个镜像源
for index_url, trusted_host in mirrors:
    print(f"\n尝试镜像源: {index_url}")
    print("-" * 60)
    
    cmd = [
        sys.executable, '-m', 'pip', 'install',
        '--index-url', index_url,
        '--trusted-host', trusted_host,
        '--timeout', '60',
        '--retries', '3',
        '-r', 'requirements.txt'
    ]
    
    try:
        result = subprocess.run(
            cmd, 
            env=env, 
            check=True,
            timeout=600,  # 10分钟超时
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("\n" + "=" * 60)
        print("✓ 依赖安装成功！")
        print("=" * 60)
        if result.stdout:
            print("输出:")
            print(result.stdout[-500:])  # 只显示最后500字符
        sys.exit(0)
        
    except subprocess.TimeoutExpired:
        print(f"✗ 安装超时（超过10分钟）")
        continue
    except subprocess.CalledProcessError as e:
        print(f"✗ 安装失败，错误代码: {e.returncode}")
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
print("2. 手动删除 PIP_NO_INDEX 环境变量")
print("3. 检查防火墙/代理设置")
sys.exit(1)
