import threading
import time
from collections import OrderedDict
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Product
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with LoggedTestClient(app) as c:
        yield c


@pytest.fixture
def sample_product(db):
    product = Product(
        product_name="中邮普惠保险",
        insurance_type="普惠保险",
        insurance_period="1年",
        payment_period="一次性缴清",
        sum_insured=100000.00,
        premium=100.00,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# ═══════════════════════════════════════════════════════════════════
# Markdown test report
# ═══════════════════════════════════════════════════════════════════

_md_test_log = {}
_test_ctx = threading.local()


def pytest_addoption(parser):
    parser.addoption(
        "--md-report",
        nargs="?",
        const="test-report.md",
        default=None,
        help="Generate markdown test report (default: test-report.md)",
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    _test_ctx.current_nodeid = item.nodeid
    _md_test_log[item.nodeid] = {
        "description": item.function.__doc__ or "",
        "calls": [],
        "outcome": None,
        "duration": 0,
    }
    yield


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    start = time.time()
    yield
    duration = time.time() - start
    if pyfuncitem.nodeid in _md_test_log:
        _md_test_log[pyfuncitem.nodeid]["duration"] = duration


def pytest_runtest_logreport(report):
    if report.nodeid in _md_test_log and report.when == "call":
        _md_test_log[report.nodeid]["outcome"] = report.outcome
        if report.failed:
            _md_test_log[report.nodeid]["longrepr"] = str(report.longrepr)


class LoggedTestClient(TestClient):
    def request(self, method, url, **kwargs):
        response = super().request(method, url, **kwargs)
        nodeid = getattr(_test_ctx, "current_nodeid", None)
        if nodeid and nodeid in _md_test_log:
            try:
                req_body = kwargs.get("json") or kwargs.get("data") or None
            except Exception:
                req_body = None
            try:
                resp_body = response.json()
            except Exception:
                resp_body = response.text[:500] if response.text else None
            _md_test_log[nodeid]["calls"].append({
                "method": method.upper(),
                "url": url,
                "request_body": req_body,
                "status_code": response.status_code,
                "response_body": resp_body,
            })
        return response


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session):
    md_path = session.config.getoption("--md-report")
    if not md_path:
        return

    total = len(_md_test_log)
    passed = sum(1 for v in _md_test_log.values() if v["outcome"] == "passed")
    failed = sum(1 for v in _md_test_log.values() if v["outcome"] == "failed")
    skipped = sum(1 for v in _md_test_log.values() if v["outcome"] == "skipped")

    lines = []
    lines.append("# Test Report\n")
    lines.append(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **总计**: {total} | ✅ 通过: {passed} | ❌ 失败: {failed} | ⏭️ 跳过: {skipped}\n")

    groups = OrderedDict()
    for nodeid, info in _md_test_log.items():
        file_part = nodeid.split("::")[0]
        test_name = nodeid.split("::")[-1]
        if file_part not in groups:
            groups[file_part] = []
        groups[file_part].append((test_name, info))

    for file_path, tests in groups.items():
        lines.append(f"## {file_path}\n")
        for test_name, info in tests:
            status_icons = {"passed": "✅", "failed": "❌", "skipped": "⏭️"}
            icon = status_icons.get(info["outcome"], "⬜")
            lines.append(f"### {test_name} {icon}")

            if info["description"]:
                lines.append(f"\n**描述**: {info['description']}")

            lines.append(f"\n**状态**: {info['outcome']} | **耗时**: {info['duration']:.3f}s\n")

            if info["outcome"] == "failed" and info.get("longrepr"):
                lines.append("**失败原因**:")
                lines.append("```")
                lines.append(info["longrepr"])
                lines.append("```\n")

            if info["calls"]:
                lines.append("**HTTP 请求记录**:\n")
                for i, call in enumerate(info["calls"], 1):
                    lines.append(f"- **{call['method']} {call['url']}** → `{call['status_code']}`")
                    if call["request_body"]:
                        import json
                        req_str = json.dumps(call["request_body"], ensure_ascii=False, indent=2)
                        lines.append(f"  - 请求体:")
                        lines.append("    ```json")
                        for ln in req_str.split("\n"):
                            lines.append(f"    {ln}")
                        lines.append("    ```")
                    if call["response_body"]:
                        resp_str = json.dumps(call["response_body"], ensure_ascii=False, indent=2)
                        lines.append(f"  - 响应体:")
                        lines.append("    ```json")
                        for ln in resp_str.split("\n"):
                            lines.append(f"    {ln}")
                        lines.append("    ```")
                lines.append("")

        lines.append("---\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nMarkdown 测试报告已生成: {md_path}")
