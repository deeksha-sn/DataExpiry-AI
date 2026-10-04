#!/usr/bin/env python3
"""
DATAEXPIRY — Database Initialization & Synthetic Seed Script
Loads synthetic data records into the database.
"""

import os
import json
import sys

# Add backend directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


from app.database.session import SessionLocal, engine, Base
from app.models.data_record import DataRecordModel

def seed_database():
    print("🔄 Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Locate records.json
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "data", "synthetic", "records.json"),
            os.path.join(os.path.dirname(__file__), "data", "synthetic", "records.json"),
            "data/synthetic/records.json",
            "../data/synthetic/records.json"
        ]

        json_path = None
        for path in possible_paths:
            if os.path.exists(path):
                json_path = path
                break

        if not json_path:
            print("⚠️ Warning: records.json not found. Skipping dataset seeding.")
            return

        print(f"📖 Reading synthetic records from: {json_path}")
        with open(json_path, "r") as f:
            records_data = json.load(f)

        existing_count = db.query(DataRecordModel).count()
        print(f"📊 Current database records count: {existing_count}")

        inserted = 0
        skipped = 0

        for item in records_data:
            rec_id = item.get("record_id")
            existing = db.query(DataRecordModel).filter(DataRecordModel.record_id == rec_id).first()
            if not existing:
                db_obj = DataRecordModel(**item)
                db.add(db_obj)
                inserted += 1
            else:
                skipped += 1

        db.commit()
        total_count = db.query(DataRecordModel).count()
        print(f"✅ Seeding complete! Inserted: {inserted}, Skipped (already exist): {skipped}, Total Records in DB: {total_count}")

        # Seed demonstration retention policies
        demo_policies = [
            {
                "rule_code": "POL-CUS-01",
                "name": "Customer Retention Demo Policy",
                "category": "Customer",
                "retention_period": "2 years",
                "retention_days": 730,
                "action_on_expiry": "REVIEW",
                "description": "Demonstration retention policy for customer records (2 years -> REVIEW)",
                "is_active": True
            },
            {
                "rule_code": "POL-TXN-01",
                "name": "Transaction Retention Demo Policy",
                "category": "Transaction",
                "retention_period": "3 years",
                "retention_days": 1095,
                "action_on_expiry": "REVIEW",
                "description": "Demonstration retention policy for transaction records (3 years -> REVIEW)",
                "is_active": True
            },
            {
                "rule_code": "POL-MKT-01",
                "name": "Marketing Retention Demo Policy",
                "category": "Marketing",
                "retention_period": "1 year",
                "retention_days": 365,
                "action_on_expiry": "DELETE",
                "description": "Demonstration retention policy for marketing records (1 year -> DELETE)",
                "is_active": True
            }
        ]

        print("📋 Checking demonstration retention policies...")
        from app.models.policy import PolicyRuleModel
        pol_inserted = 0
        pol_skipped = 0
        for pol_data in demo_policies:
            existing_pol = db.query(PolicyRuleModel).filter(
                PolicyRuleModel.rule_code == pol_data["rule_code"]
            ).first()
            if not existing_pol:
                db_pol = PolicyRuleModel(**pol_data)
                db.add(db_pol)
                pol_inserted += 1
            else:
                pol_skipped += 1

        db.commit()
        total_policies = db.query(PolicyRuleModel).count()
        print(f"✅ Policy seeding complete! Inserted: {pol_inserted}, Skipped: {pol_skipped}, Total Policies: {total_policies}")


    except Exception as e:
        db.rollback()
        print(f"❌ Error during database seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
