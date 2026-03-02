# -*- coding: utf-8 -*-
"""
检查工作时间设置和算法逻辑
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models

db = SessionLocal()

print("="*80)
print("检查工作时间设置")
print("="*80)

# 当前时间
now = datetime.now()
print(f"\n当前系统时间: {now}")
print(f"当前小时: {now.hour}")

# 检查资源产能
resource = db.query(models.Resource).filter(models.Resource.id == 3).first()
if resource:
    print(f"\n资源 CNC机床-3 产能: {resource.capacity_per_day} 小时/天")
    
    work_start_hour = 8
    work_end_hour = work_start_hour + int(resource.capacity_per_day)
    
    print(f"\n工作时间设置:")
    print(f"  - 开始: {work_start_hour}:00")
    print(f"  - 结束: {work_end_hour}:00")
    
    if now.hour < work_start_hour:
        print(f"\n当前时间 ({now.hour}:00) 在工作开始之前")
        print(f"排程会从今天 {work_start_hour}:00 开始")
    elif now.hour >= work_end_hour:
        print(f"\n当前时间 ({now.hour}:00) 已超过工作结束时间")
        print(f"排程会从明天 {work_start_hour}:00 开始")
    else:
        print(f"\n当前时间 ({now.hour}:00) 在工作时间内")
        print(f"排程会从今天 {now.hour}:00 开始")

db.close()
