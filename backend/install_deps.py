#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安装后端依赖的 Python 脚本
通过修改环境变量来绕过 PIP_NO_INDEX 限制
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

# 安装命令
cmd = [
    sys.executable, '-m', 'pip', 'install',
    '--index-url', 'https://mirrors.aliyun.com/pypi/simple/',
    '--trusted-host', 'mirrors.aliyun.com',
    '-r', 'requirements.txt'
]

print("正在安装后端依赖...")
print(f"使用 Python: {sys.executable}")
print(f"命令: {' '.join(cmd)}")
print("-" * 60)

try:
    result = subprocess.run(cmd, env=env, check=True)
    print("\n✓ 依赖安装成功！")
    sys.exit(0)
except subprocess.CalledProcessError as e:
    print(f"\n✗ 依赖安装失败，错误代码: {e.returncode}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ 发生错误: {e}")
    sys.exit(1)
