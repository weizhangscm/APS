# APS 排程系统

一个参考 SAP PPDS 设计的工序级高级计划排程系统，支持甘特图可视化、有限产能排程、拖拽调整和 KPI 仪表板。

## 功能特性

### 核心排程功能
- **正向排程**: 从最早开始时间向后排程
- **逆向排程**: 从交货期向前排程
- **有限产能**: 考虑资源每日可用产能进行排程
- **优先级规则**: 支持 EDD(最早交期)、SPT(最短加工时间)、FIFO(先进先出)等规则

### 可视化功能
- **订单甘特图**: 按订单显示所有工序的排程情况
- **资源甘特图**: 按资源显示负荷分布
- **拖拽调整**: 支持直接拖拽工序调整排程
- **实时约束检测**: 拖拽时自动检测资源冲突和顺序约束

### 约束管理
- 资源产能约束
- 工序顺序约束
- 最早开始时间约束
- 交货期约束检测

### KPI 仪表板
- 资源利用率统计
- 订单准时率
- 平均提前期
- 每日产能负荷图表

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue.js 3 + Vite |
| UI 组件库 | Element Plus |
| 甘特图 | DHTMLX Gantt |
| 图表 | ECharts + vue-echarts |
| 状态管理 | Pinia |
| 后端框架 | Python FastAPI |
| 数据库 | SQLite + SQLAlchemy |

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 18+

### 安装步骤

1. **克隆项目**
```bash
cd "APS Test"
```

2. **安装后端依赖**
```bash
cd backend
pip install -r requirements.txt
```

3. **初始化演示数据**
```bash
python init_demo_data.py
```

4. **启动后端服务**
```bash
uvicorn app.main:app --reload --port 8000
```

5. **安装前端依赖**（新开终端）
```bash
cd frontend
npm install
```

6. **启动前端开发服务器**
```bash
npm run dev
```

7. **访问系统**

打开浏览器访问: http://localhost:3000

## 项目结构

```
APS Test/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── models.py            # 数据库模型
│   │   ├── schemas.py           # Pydantic 模式
│   │   ├── database.py          # 数据库连接
│   │   ├── routers/
│   │   │   ├── master_data.py   # 主数据 API
│   │   │   ├── orders.py        # 订单 API
│   │   │   └── scheduling.py    # 排程 API
│   │   └── scheduler/
│   │       ├── engine.py        # 排程引擎
│   │       ├── algorithms.py    # 排程算法
│   │       └── constraints.py   # 约束检测
│   ├── init_demo_data.py        # 演示数据初始化
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   ├── components/          # 通用组件
│   │   ├── api/                 # API 调用
│   │   ├── stores/              # Pinia 状态管理
│   │   └── styles/              # 样式文件
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## API 文档

启动后端服务后，访问 http://localhost:8000/docs 查看 Swagger API 文档。

### 主要 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/master-data/work-centers` | GET/POST | 工作中心管理 |
| `/api/master-data/resources` | GET/POST | 资源管理 |
| `/api/master-data/products` | GET/POST | 产品管理 |
| `/api/master-data/routings` | GET/POST | 工艺路线管理 |
| `/api/orders/` | GET/POST | 生产订单管理 |
| `/api/scheduling/run` | POST | 执行排程 |
| `/api/scheduling/gantt-data` | GET | 获取甘特图数据 |
| `/api/scheduling/kpi` | GET | 获取 KPI 数据 |

## 使用说明

### 1. 主数据配置

首先配置基础主数据:
1. **工作中心**: 定义生产车间或区域
2. **资源**: 定义具体的机器或工人，设置日产能
3. **产品**: 定义产品信息
4. **工艺路线**: 为产品定义生产工序和加工时间

### 2. 创建生产订单

在订单管理界面创建生产订单，系统会自动根据工艺路线生成工序。

### 3. 执行排程

在甘特图页面:
1. 选择排程方向（正向/逆向）
2. 选择优先级规则
3. 选择是否考虑有限产能
4. 点击"执行排程"

### 4. 调整排程

- 直接拖拽甘特图上的工序条调整时间
- 系统会自动检测约束违反并提示

### 5. 查看 KPI

在仪表板页面查看:
- 资源利用率
- 订单准时率
- 产能负荷分布

## 数据模型

```
工作中心 (WorkCenter)
  └── 资源 (Resource)
        └── 工序实例 (Operation)

产品 (Product)
  └── 工艺路线 (Routing)
        └── 工艺工序 (RoutingOperation)

生产订单 (ProductionOrder)
  └── 工序实例 (Operation)
```

## 许可证

MIT License

##test