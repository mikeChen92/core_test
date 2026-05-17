# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 构建与运行

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务
uvicorn app.main:app --reload

# 运行全部测试
pytest -v

# 运行单个测试文件
pytest tests/test_underwriting.py -v

# 运行单个测试用例
pytest tests/test_underwriting.py::test_submit_underwriting_success -v

# 运行测试并生成 JUnit XML 报告
pytest -v --junitxml=test-report.xml

# 运行测试并生成 Markdown 详细报告（含请求/响应详情）
pytest -v --md-report

# 运行测试并同时生成 XML + Markdown 报告
pytest -v --junitxml=test-report.xml --md-report=test-report.md
```

## 技术栈

- **FastAPI** (0.115) — Web 框架
- **SQLAlchemy** (2.0) — ORM，开发/生产用 MySQL（阿里云 RDS），测试用 SQLite :memory:
- **Pydantic v2** — 请求/响应模型校验
- **pytest** (8.3) + `TestClient` — 集成测试，使用内存 SQLite
- **httpx** / **BeautifulSoup** / **lxml** — 网页抓取
- **Jinja2** — 收银台页面模板

## 项目架构

四模块保险核心系统，分层结构：

```
app/main.py          → FastAPI 应用入口，注册路由
app/database.py      → SQLAlchemy 引擎 / 会话 / Base
app/models.py        → 4 个 ORM 模型：Product, UnderwritingRecord, Policy, PaymentRecord
app/schemas.py       → Pydantic 请求/响应模型
app/api/*.py         → API 路由层（薄层，委托给 services）
app/services/*.py    → 业务逻辑层（以自定义 *Error 异常向外传递错误）
app/scraper/*.py     → 产品信息网页抓取
app/templates/*.html → 收银台页面（Jinja2 模板）
tests/               → 集成测试，使用 SQLite :memory:，每个测试后清空
```

## 业务流程

```
抓取产品 → 产品列表 → 核保申请 → 核保通过 → 生成保单 → 创建支付 → 收银台支付 → 回调通知
```

**核保规则**（`app/services/underwriting.py`）：
- 被保人年龄必须在 18–65 周岁
- 同一被保人身份证号不能存在未结清的拒保记录
- 拒保记录会先持久化再抛出异常

**出单规则**（`app/services/policy.py`）：
- 仅核保通过的记录可以出单
- 每条核保记录最多生成一张保单
- 保单号格式：`P{YYYYMMDD}{6位序列号}`

**支付规则**（`app/services/payment.py`）：
- 一张保单最多有一个待支付订单
- 订单号格式：`ORD{YYYYMMDDHHmmSS}{4位序列号}`
- 用户确认支付后通过 BackgroundTasks 异步回调前端

## 数据库

- **开发/生产**：阿里云 RDS MySQL（`db_test1`），连接信息在 `.env` 中配置
- **测试**：SQLite `:memory:`，通过 `conftest.py` 注入覆盖
- **连接配置**：`app/database.py` 根据 `DATABASE_URL` 前缀自动适配 SQLite/MySQL 的 `connect_args`

## 测试规范

- `conftest.py` 提供 `client`（TestClient，已注入测试用 DB）、`db`（会话）、`sample_product`（产品 fixture）
- `setup_db` autouse fixture：每个测试前建表，测试后删表
- 抓取相关测试需要 mock `app.api.products.scrape_product`，避免真实 HTTP 请求

## 错误处理

所有 API 接口返回统一错误结构：
```json
{"detail": {"code": "ERROR_CODE", "message": "描述"}}
```
业务错误 = 400，资源不存在 = 404，抓取失败 = 502，参数校验失败 = 422。
