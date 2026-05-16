from fastapi import FastAPI
from app.database import engine, Base
from app.api import products, underwriting, policies, payments

Base.metadata.create_all(bind=engine)

app = FastAPI(title="保险公司核心系统", version="1.0.0")

app.include_router(products.router)
app.include_router(underwriting.router)
app.include_router(policies.router)
app.include_router(payments.router)
app.include_router(payments.page_router)


@app.get("/health")
def health():
    return {"status": "ok"}
