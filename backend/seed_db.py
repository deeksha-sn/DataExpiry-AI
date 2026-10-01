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

    except Exception as e:
        db.rollback()
        print(f"❌ Error during database seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
