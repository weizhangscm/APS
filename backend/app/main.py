from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import init_db, SessionLocal
from .routers import master_data, orders, scheduling, setup_matrix, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup: Initialize database
    init_db()
    
    # Initialize default admin user
    db = SessionLocal()
    try:
        auth.init_default_user(db)
    finally:
        db.close()
    
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="APS排程系统",
    description="工序级高级计划排程系统 - 参考SAP PPDS设计",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["用户认证"])
app.include_router(master_data.router, prefix="/api/master-data", tags=["主数据管理"])
app.include_router(orders.router, prefix="/api/orders", tags=["生产订单"])
app.include_router(scheduling.router, prefix="/api/scheduling", tags=["排程管理"])
app.include_router(setup_matrix.router, prefix="/api/setup-matrix", tags=["切换矩阵"])


@app.get("/")
def root():
    return {
        "message": "APS排程系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
