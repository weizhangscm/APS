from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sqlite3

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aps.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _sqlite_migrate_columns():
    """为已有 SQLite 库追加 ORM 新增列（create_all 不会改已有表结构）"""
    if not os.path.isfile(DB_PATH):
        return
    alters = [
        ("resources", "location", "VARCHAR(50)"),
        ("resources", "operating_start", "VARCHAR(30)"),
        ("resources", "operating_end", "VARCHAR(30)"),
        ("resources", "operating_break", "VARCHAR(30)"),
        ("resources", "operating_rest_start", "VARCHAR(30)"),
        ("resources", "operating_rest_end", "VARCHAR(30)"),
        ("resources", "utilization_percent", "FLOAT"),
        ("resources", "production_hours", "FLOAT"),
        ("resources", "capacity_value", "FLOAT"),
        ("resources", "finite_planning", "INTEGER DEFAULT 1"),
        ("resources", "is_bottleneck", "INTEGER DEFAULT 0"),
        ("resources", "timezone", "VARCHAR(50)"),
        ("resources", "factory_calendar", "VARCHAR(50)"),
        ("resources", "planning_group", "VARCHAR(50)"),
        ("products", "product_type", "VARCHAR(20)"),
        ("products", "location", "VARCHAR(50)"),
        ("products", "location_name", "VARCHAR(100)"),
        ("products", "mrp_controller", "VARCHAR(20)"),
        ("products", "mrp_controller_name", "VARCHAR(100)"),
        ("products", "deletion_flag", "INTEGER DEFAULT 0"),
        ("routings", "location", "VARCHAR(50)"),
        ("production_orders", "location", "VARCHAR(50)"),
        ("shifts", "location", "VARCHAR(50)"),
        ("shifts", "break_start_time", "VARCHAR(10)"),
        ("shifts", "break_end_time", "VARCHAR(10)"),
        ("setup_matrix", "location", "VARCHAR(50)"),
        ("users", "department", "VARCHAR(100)"),
        ("users", "date_format", "VARCHAR(40)"),
        ("users", "time_format", "VARCHAR(10)"),
        ("users", "user_timezone", "VARCHAR(80)"),
    ]
    conn = sqlite3.connect(DB_PATH)
    try:
        for table, col, typ in alters:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
                conn.commit()
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    conn.rollback()
                    raise
    finally:
        conn.close()


def _sqlite_locations_master_table():
    if not os.path.isfile(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                code VARCHAR(50) PRIMARY KEY,
                description VARCHAR(200),
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _migrate_legacy_default_location_code():
    """将业务表 location=DEFAULT 改为 1001，并删除 locations 主数据中的 DEFAULT。"""
    if not os.path.isfile(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='locations'"
        )
        if not cur.fetchone():
            return
        for table in (
            "products",
            "resources",
            "routings",
            "production_orders",
            "shifts",
            "setup_matrix",
        ):
            cur.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
            if not cur.fetchone():
                continue
            try:
                cur.execute(
                    f'UPDATE "{table}" SET location = ? WHERE location = ?',
                    ("1001", "DEFAULT"),
                )
            except sqlite3.OperationalError as e:
                if "no such column" not in str(e).lower():
                    raise
        cur.execute("DELETE FROM locations WHERE code = 'DEFAULT'")
        conn.commit()
    except Exception as ex:
        conn.rollback()
        print(f"legacy DEFAULT location migration: {ex}")
    finally:
        conn.close()


def _bootstrap_location_catalog():
    from . import models
    from .services.location_catalog import PRIMARY_LOCATION_CODE

    db = SessionLocal()
    try:
        if (
            db.query(models.Location)
            .filter(models.Location.code == PRIMARY_LOCATION_CODE)
            .first()
            is None
        ):
            db.add(
                models.Location(
                    code=PRIMARY_LOCATION_CODE,
                    description="默认位置",
                )
            )
            db.commit()

        codes = set()
        for row in db.query(models.Product.location).filter(models.Product.location.isnot(None)).all():
            c = (row[0] or "").strip()
            if c:
                codes.add(c)
        for row in db.query(models.Resource.location).filter(models.Resource.location.isnot(None)).all():
            c = (row[0] or "").strip()
            if c:
                codes.add(c)
        for code in codes:
            if db.query(models.Location).filter(models.Location.code == code).first() is None:
                db.add(models.Location(code=code, description=None))
        db.commit()

        for r in db.query(models.Routing).all():
            if not (getattr(r, "location", None) or "").strip():
                r.location = PRIMARY_LOCATION_CODE
        for m in db.query(models.SetupMatrix).all():
            if not (getattr(m, "location", None) or "").strip():
                m.location = PRIMARY_LOCATION_CODE
        for s in db.query(models.Shift).all():
            if not (getattr(s, "location", None) or "").strip():
                s.location = PRIMARY_LOCATION_CODE
        for o in db.query(models.ProductionOrder).all():
            if not (getattr(o, "location", None) or "").strip():
                p = (
                    db.query(models.Product)
                    .filter(models.Product.id == o.product_id)
                    .first()
                )
                if p and (p.location or "").strip():
                    o.location = (p.location or "").strip()
                else:
                    o.location = PRIMARY_LOCATION_CODE
        db.commit()
    except Exception as ex:
        db.rollback()
        print(f"location catalog bootstrap skipped: {ex}")
    finally:
        db.close()


def _sqlite_routing_operations_work_center_nullable():
    """routing_operations.work_center_id 改为可空（仅指定资源、无工作中心时）"""
    if not os.path.isfile(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='routing_operations'"
        )
        if not cur.fetchone():
            return
        cur.execute("PRAGMA table_info(routing_operations)")
        rows = cur.fetchall()
        wc = next((r for r in rows if r[1] == "work_center_id"), None)
        if not wc or wc[3] == 0:
            return
        cur.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='routing_operations' AND sql IS NOT NULL"
        )
        index_sqls = [r[0] for r in cur.fetchall() if r[0]]
        colnames = ", ".join(f'"{r[1]}"' for r in rows)

        def coldef(r):
            _cid, name, ctype, notnull, dflt, pk = r
            if name == "work_center_id":
                notnull = 0
            ctype = ctype or "TEXT"
            if name == "id" and pk == 1:
                return '"id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT'
            parts = [f'"{name}"', ctype]
            if pk == 1:
                parts.append("PRIMARY KEY")
            if notnull == 1:
                parts.append("NOT NULL")
            if dflt is not None and not (name == "id" and pk == 1):
                parts.append(f"DEFAULT {dflt}")
            return " ".join(parts)

        defs = ", ".join(coldef(r) for r in rows)
        cur.execute("PRAGMA foreign_keys=OFF")
        cur.execute("DROP TABLE IF EXISTS routing_operations__wc_fix")
        cur.execute(f"CREATE TABLE routing_operations__wc_fix ({defs})")
        cur.execute(
            f"INSERT INTO routing_operations__wc_fix ({colnames}) SELECT {colnames} FROM routing_operations"
        )
        cur.execute("DROP TABLE routing_operations")
        cur.execute("ALTER TABLE routing_operations__wc_fix RENAME TO routing_operations")
        for sql in index_sqls:
            try:
                cur.execute(sql)
            except sqlite3.OperationalError:
                pass
        conn.commit()
    except Exception as ex:
        conn.rollback()
        print(f"routing_operations work_center_id nullable migration skipped: {ex}")
    finally:
        conn.close()


def _sqlite_resources_work_center_nullable():
    """将 resources.work_center_id 改为可空（SQLite 无法 ALTER COLUMN，需重建表）"""
    if not os.path.isfile(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='resources'"
        )
        if not cur.fetchone():
            return
        cur.execute("PRAGMA table_info(resources)")
        rows = cur.fetchall()
        wc = next((r for r in rows if r[1] == "work_center_id"), None)
        if not wc or wc[3] == 0:
            return
        cur.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='resources' AND sql IS NOT NULL"
        )
        index_sqls = [r[0] for r in cur.fetchall() if r[0]]
        colnames = ", ".join(f'"{r[1]}"' for r in rows)

        def coldef(r):
            _cid, name, ctype, notnull, dflt, pk = r
            if name == "work_center_id":
                notnull = 0
            ctype = ctype or "TEXT"
            if name == "id" and pk == 1:
                return '"id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT'
            parts = [f'"{name}"', ctype]
            if pk == 1:
                parts.append("PRIMARY KEY")
            if notnull == 1:
                parts.append("NOT NULL")
            if dflt is not None and not (name == "id" and pk == 1):
                parts.append(f"DEFAULT {dflt}")
            return " ".join(parts)

        defs = ", ".join(coldef(r) for r in rows)
        cur.execute("PRAGMA foreign_keys=OFF")
        cur.execute("DROP TABLE IF EXISTS resources__wc_fix")
        cur.execute(f"CREATE TABLE resources__wc_fix ({defs})")
        cur.execute(
            f"INSERT INTO resources__wc_fix ({colnames}) SELECT {colnames} FROM resources"
        )
        cur.execute("DROP TABLE resources")
        cur.execute("ALTER TABLE resources__wc_fix RENAME TO resources")
        for sql in index_sqls:
            try:
                cur.execute(sql)
            except sqlite3.OperationalError:
                pass
        conn.commit()
    except Exception as ex:
        conn.rollback()
        print(f"resources work_center_id nullable migration skipped: {ex}")
    finally:
        conn.close()


def _sqlite_resources_drop_efficiency_column():
    """删除 resources.efficiency；utilization_percent 为空时用 efficiency*100 回填。"""
    if not os.path.isfile(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='resources'"
        )
        if not cur.fetchone():
            return
        cur.execute("PRAGMA table_info(resources)")
        rows = list(cur.fetchall())
        if not any(r[1] == "efficiency" for r in rows):
            return
        try:
            cur.execute(
                "UPDATE resources SET utilization_percent = ROUND(CAST(efficiency AS REAL) * 100.0, 6) "
                "WHERE utilization_percent IS NULL AND efficiency IS NOT NULL"
            )
        except sqlite3.OperationalError:
            pass
        conn.commit()

        cur.execute("PRAGMA table_info(resources)")
        rows = list(cur.fetchall())
        rows_wo = [r for r in rows if r[1] != "efficiency"]
        cur.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='resources' AND sql IS NOT NULL"
        )
        index_sqls = [r[0] for r in cur.fetchall() if r[0]]
        colnames = ", ".join(f'"{r[1]}"' for r in rows_wo)

        def coldef(r):
            _cid, name, ctype, notnull, dflt, pk = r
            ctype = ctype or "TEXT"
            if name == "id" and pk == 1:
                return '"id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT'
            parts = [f'"{name}"', ctype]
            if pk == 1:
                parts.append("PRIMARY KEY")
            if notnull == 1:
                parts.append("NOT NULL")
            if dflt is not None and not (name == "id" and pk == 1):
                parts.append(f"DEFAULT {dflt}")
            return " ".join(parts)

        defs = ", ".join(coldef(r) for r in rows_wo)
        cur.execute("PRAGMA foreign_keys=OFF")
        cur.execute("DROP TABLE IF EXISTS resources__eff_drop")
        cur.execute(f"CREATE TABLE resources__eff_drop ({defs})")
        cur.execute(
            f"INSERT INTO resources__eff_drop ({colnames}) SELECT {colnames} FROM resources"
        )
        cur.execute("DROP TABLE resources")
        cur.execute("ALTER TABLE resources__eff_drop RENAME TO resources")
        for sql in index_sqls:
            try:
                cur.execute(sql)
            except sqlite3.OperationalError:
                pass
        conn.commit()
    except Exception as ex:
        conn.rollback()
        print(f"resources drop efficiency column migration skipped: {ex}")
    finally:
        conn.close()


def init_db():
    """Initialize database tables"""
    from . import models
    Base.metadata.create_all(bind=engine)
    _sqlite_migrate_columns()
    _sqlite_locations_master_table()
    _migrate_legacy_default_location_code()
    _bootstrap_location_catalog()
    _sqlite_routing_operations_work_center_nullable()
    _sqlite_resources_work_center_nullable()
    _sqlite_resources_drop_efficiency_column()
