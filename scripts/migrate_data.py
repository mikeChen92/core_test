"""Migrate data from SQLite to MySQL."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Product, UnderwritingRecord, Policy, PaymentRecord

# SQLite (source)
SQLITE_URL = "sqlite:///./insurance_core.db"
sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SQLiteSession = sessionmaker(bind=sqlite_engine)

# MySQL (target)
MYSQL_URL = os.getenv("DATABASE_URL", "")
if not MYSQL_URL:
    print("Error: DATABASE_URL not set")
    sys.exit(1)

mysql_engine = create_engine(MYSQL_URL)
MySQLSession = sessionmaker(bind=mysql_engine)


def migrate():
    # Create tables in MySQL
    print("Creating MySQL tables...")
    Base.metadata.create_all(bind=mysql_engine)

    sqlite_session = SQLiteSession()
    mysql_session = MySQLSession()

    try:
        # 1. Migrate Products
        print("Migrating products...")
        products = sqlite_session.query(Product).all()
        for p in products:
            mysql_session.add(Product(
                id=p.id,
                product_name=p.product_name,
                insurance_type=p.insurance_type,
                insurance_period=p.insurance_period,
                payment_period=p.payment_period,
                sum_insured=p.sum_insured,
                premium=p.premium,
                created_at=p.created_at,
            ))
        mysql_session.commit()
        print(f"  -> {len(products)} products migrated")

        # 2. Migrate UnderwritingRecords
        print("Migrating underwriting records...")
        records = sqlite_session.query(UnderwritingRecord).all()
        for r in records:
            mysql_session.add(UnderwritingRecord(
                id=r.id,
                product_id=r.product_id,
                applicant_name=r.applicant_name,
                applicant_id_no=r.applicant_id_no,
                insured_name=r.insured_name,
                insured_id_no=r.insured_id_no,
                insured_age=r.insured_age,
                status=r.status,
                reject_reason=r.reject_reason,
                created_at=r.created_at,
            ))
        mysql_session.commit()
        print(f"  -> {len(records)} underwriting records migrated")

        # 3. Migrate Policies
        print("Migrating policies...")
        policies = sqlite_session.query(Policy).all()
        for po in policies:
            mysql_session.add(Policy(
                id=po.id,
                policy_no=po.policy_no,
                underwriting_id=po.underwriting_id,
                product_id=po.product_id,
                status=po.status,
                effective_date=po.effective_date,
                expiry_date=po.expiry_date,
                created_at=po.created_at,
            ))
        mysql_session.commit()
        print(f"  -> {len(policies)} policies migrated")

        # 4. Migrate PaymentRecords
        print("Migrating payment records...")
        payments = sqlite_session.query(PaymentRecord).all()
        for pm in payments:
            mysql_session.add(PaymentRecord(
                id=pm.id,
                policy_id=pm.policy_id,
                order_no=pm.order_no,
                amount=pm.amount,
                status=pm.status,
                callback_url=pm.callback_url,
                paid_at=pm.paid_at,
                created_at=pm.created_at,
            ))
        mysql_session.commit()
        print(f"  -> {len(payments)} payment records migrated")

        print("\nMigration completed successfully!")
    except Exception as e:
        mysql_session.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        sqlite_session.close()
        mysql_session.close()


if __name__ == "__main__":
    migrate()
