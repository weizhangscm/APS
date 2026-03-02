"""一次性迁移：为 routing_operations 表添加 resource_id 列。在 backend 目录执行: python add_routing_operation_resource_id.py"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "aps.db")

def main():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}，跳过")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(routing_operations)")
    columns = [row[1] for row in cur.fetchall()]
    if "resource_id" in columns:
        print("routing_operations.resource_id 已存在，跳过")
    else:
        cur.execute("ALTER TABLE routing_operations ADD COLUMN resource_id INTEGER REFERENCES resources(id)")
        conn.commit()
        print("已添加 routing_operations.resource_id")
    conn.close()

if __name__ == "__main__":
    main()
