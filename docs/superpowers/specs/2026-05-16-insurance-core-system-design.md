# 保险公司核心系统 - 设计文档

## 概述

构建一个简单的保险公司核心系统，包含产品信息、核保、承保、支付四个模块。提供 REST API 接口。

- 技术栈：Python + FastAPI + MySQL + SQLAlchemy + BeautifulSoup
- 产品信息通过网页抓取获取
- 支付为示意功能，模拟收银台流程

## 数据模型

### products（产品表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| product_name | String(200) | 产品名称 |
| insurance_type | String(100) | 险种 |
| insurance_period | String(100) | 保险期间 |
| payment_period | String(100) | 缴费期间 |
| sum_insured | Decimal(12,2) | 保额 |
| premium | Decimal(10,2) | 保费 |
| created_at | DateTime | 创建时间 |

### underwriting_records（核保记录表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| product_id | Integer FK | 关联产品 |
| applicant_name | String(100) | 投保人姓名 |
| applicant_id_no | String(18) | 投保人身份证号 |
| insured_name | String(100) | 被保人姓名 |
| insured_id_no | String(18) | 被保人身份证号 |
| insured_age | Integer | 被保人年龄 |
| status | Enum | pending / approved / rejected |
| reject_reason | Text | 拒保原因 |
| created_at | DateTime | 创建时间 |

### policies（保单表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| policy_no | String(50) | 保单号（唯一） |
| underwriting_id | Integer FK | 关联核保记录 |
| product_id | Integer FK | 关联产品 |
| status | Enum | active / cancelled |
| effective_date | Date | 生效日期 |
| expiry_date | Date | 到期日期 |
| created_at | DateTime | 创建时间 |

### payment_records（支付记录表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| policy_id | Integer FK | 关联保单 |
| order_no | String(50) | 订单号（唯一） |
| amount | Decimal(10,2) | 支付金额 |
| status | Enum | pending / success / failed |
| callback_url | String(500) | 回调地址 |
| paid_at | DateTime | 支付时间 |
| created_at | DateTime | 创建时间 |

## API 接口

### 产品模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/products/scrape` | 触发抓取产品信息 |
| GET | `/api/products` | 产品列表 |
| GET | `/api/products/{id}` | 产品详情 |

### 核保模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/underwriting` | 提交核保申请 |
| GET | `/api/underwriting/{id}` | 查询核保结果 |

核保规则（示意）：
- 被保人年龄在 18-65 周岁之间
- 同一被保人没有未结清的拒保记录
- 通过则 status=approved，否则 status=rejected + reject_reason

### 承保模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/policies` | 核保通过后生成保单 |
| GET | `/api/policies/{id}` | 查询保单详情 |
| GET | `/api/policies` | 保单列表 |

保单号规则：`P{YYYYMMDD}{6位序列号}`

### 支付模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/payments/create` | 创建支付订单，返回支付链接 |
| POST | `/api/payments/callback` | 支付回调接口 |
| GET | `/api/payments/{id}` | 查询支付记录 |

## 支付流程

1. 前端调用 `POST /api/payments/create`，传入 `policy_id` 和 `callback_url`
2. 系统生成支付记录（status=pending），返回 `{payment_url: /payment/{order_no}}`
3. 前端跳转到收银台页面 `/payment/{order_no}`
4. 收银台页面展示保单号和金额，用户点击"确认支付"
5. 系统模拟支付成功：
   - 更新支付记录 status=success, paid_at=now
   - 重定向到 `callback_url?order_no=xxx&status=success`
   - 异步 POST 请求 `callback_url` 通知支付状态（JSON body）
6. 前端收到回调后处理后续业务

## 网页抓取

- 技术：httpx + BeautifulSoup
- 目标页面提取字段：产品名称、险种、保险期间、缴费期间、保额、保费
- 手动触发（POST /api/products/scrape），不和定时任务绑定
- 新抓取数据覆盖原有产品数据（仅一个产品）

## 项目结构

```
core_test/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── database.py          # 数据库连接 + session 管理
│   ├── models.py            # SQLAlchemy 模型
│   ├── schemas.py           # Pydantic 请求/响应模型
│   ├── api/
│   │   ├── __init__.py
│   │   ├── products.py      # 产品路由
│   │   ├── underwriting.py  # 核保路由
│   │   ├── policies.py      # 承保路由
│   │   └── payments.py      # 支付路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── underwriting.py  # 核保业务逻辑
│   │   ├── policy.py        # 承保业务逻辑
│   │   └── payment.py       # 支付业务逻辑
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── scraper.py       # 网页抓取
│   └── templates/
│       └── checkout.html    # 收银台页面
├── requirements.txt
└── .env                     # 数据库配置
```

## 错误处理

统一错误格式：
```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

HTTP 状态码：
- 200 - 成功
- 400 - 请求参数错误/核保拒绝
- 404 - 资源不存在
- 409 - 冲突（如重复支付）
- 500 - 服务器内部错误

## 测试策略

- pytest + httpx (TestClient)
- 每条 API 路径至少覆盖成功场景和主要错误场景
- 测试数据库使用 SQLite 内存模式
