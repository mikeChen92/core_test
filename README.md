# 保险公司核心系统

基于 FastAPI + SQLAlchemy 的保险核心业务系统，涵盖产品管理、核保、承保、支付四个核心模块。

## 技术栈

- **FastAPI** — Web 框架
- **SQLAlchemy** 2.0 — ORM
- **MySQL** (阿里云 RDS) / **SQLite** (测试)
- **Pydantic v2** — 数据校验
- **pytest** + TestClient — 集成测试

## 业务流程

```
抓取产品 → 产品列表 → 核保申请 → 核保通过 → 生成保单 → 创建支付 → 收银台支付 → 回调通知
```

## 快速开始

```bash
# 克隆仓库
git clone git@github.com:mikeChen92/core_test.git
cd core_test

# 安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置数据库
# 编辑 .env，设置 DATABASE_URL（默认连接 MySQL RDS）

# 启动服务
uvicorn app.main:app --reload

# 访问接口文档
# http://localhost:8000/docs
```

## 测试

```bash
pytest -v
```

测试使用 SQLite 内存数据库，无需外部数据库依赖。

## 项目结构

```
app/
├── main.py           # 应用入口
├── database.py       # 数据库引擎配置
├── models.py         # ORM 模型（Product / UnderwritingRecord / Policy / PaymentRecord）
├── schemas.py        # Pydantic 请求/响应模型
├── api/              # API 路由
│   ├── products.py
│   ├── underwriting.py
│   ├── policies.py
│   └── payments.py
├── services/         # 业务逻辑
│   ├── underwriting.py
│   ├── policy.py
│   └── payment.py
├── scraper/          # 网页抓取
└── templates/        # 收银台页面
tests/                # 集成测试
scripts/              # 工具脚本
```

## API 概览

| 模块 | 端点 | 说明 |
|------|------|------|
| 产品 | `POST /api/products/scrape` | 从网页抓取产品信息 |
| 产品 | `GET /api/products` | 产品列表 |
| 产品 | `GET /api/products/{id}` | 产品详情 |
| 核保 | `POST /api/underwriting` | 提交核保申请 |
| 核保 | `GET /api/underwriting/{id}` | 查询核保结果 |
| 承保 | `POST /api/policies` | 生成保单 |
| 承保 | `GET /api/policies` | 保单列表 |
| 承保 | `GET /api/policies/{id}` | 保单详情 |
| 支付 | `POST /api/payments/create` | 创建支付订单 |
| 支付 | `POST /api/payments/callback` | 支付回调 |
| 支付 | `GET /api/payments/{id}` | 查询支付记录 |
| 页面 | `GET /payment/{order_no}` | 收银台页面 |
| 页面 | `POST /payment/{order_no}/confirm` | 确认支付 |

完整 API 接口文档见 [API.md](API.md)。

## 核保规则

- 被保人年龄须在 18–65 周岁
- 同一被保人不能存在未结清的拒保记录
