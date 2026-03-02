"""
诊断：脚本使用的数据库路径 + CNC机床-1 上已排程工序数，用于对比界面是否连同一库。
"""
import sys
import os
sys.path.insert(0, '.')

# 先取 DB 路径（与 app.database 一致）
from app.database import engine, DB_PATH, SQLALCHEMY_DATABASE_URL
db_abs = os.path.abspath(DB_PATH)
print("=== DB path (script / app.database) ===")
print("DB_PATH (relative):", DB_PATH)
print("DB_PATH (absolute):", db_abs)
print("SQLALCHEMY_DATABASE_URL:", SQLALCHEMY_DATABASE_URL)
print("File exists:", os.path.isfile(db_abs))
print()

from app.database import SessionLocal
from app import models

db = SessionLocal()
try:
    # CNC机床-1 的 resource_id（一般为 1，按名称查更稳）
    r = db.query(models.Resource).filter(models.Resource.name == "CNC机床-1").first()
    if not r:
        print("Resource CNC机床-1 not found.")
    else:
        rid = r.id
        # 该资源上已排程工序数（scheduled_start 非空）
        count = db.query(models.Operation).filter(
            models.Operation.resource_id == rid,
            models.Operation.scheduled_start != None
        ).count()
        print("=== CNC机床-1 existing schedule (in DB) ===")
        print("Resource id:", rid)
        print("Operations with scheduled_start (count):", count)
        if count > 0:
            from sqlalchemy import func
            rows = db.query(
                models.Operation.id,
                models.Operation.order_id,
                models.Operation.scheduled_start,
                models.Operation.scheduled_end
            ).filter(
                models.Operation.resource_id == rid,
                models.Operation.scheduled_start != None
            ).order_by(models.Operation.scheduled_start).limit(10).all()
            print("Sample (up to 10):")
            for row in rows:
                print("  op_id=%s order_id=%s start=%s end=%s" % (row[0], row[1], row[2], row[3]))
finally:
    db.close()

print()
print("=== 结论（脚本 vs 界面）===")
print("脚本与界面使用同一数据库：backend 通过 app.database 的 DB_PATH 连接，")
print("路径由 __file__(app/database.py) 解析，与运行目录无关，故脚本与 uvicorn 连的是同一 aps.db。")
print("若「取消计划」后在界面能排多单、脚本直接跑只排 1 单：")
print("  原因 = 操作顺序不同。界面先点「取消计划」清空该资源上计划订单的排程，再跑启发式时库里空档多；")
print("  脚本若未先取消，库里仍有已排程工序，显示区间内空档少，故只排上 1 单。")
print("建议：脚本需与界面一致时，先调用取消计划（如 engine.cancel_plan(resource_ids=...)）再跑启发式。")
