#!/usr/bin/env python3
"""
DATAEXPIRY — Synthetic Data Generator
Generates realistic, non-PII synthetic data records for testing and development.
"""

import json
import random
import argparse
from datetime import datetime, timedelta

CATEGORIES = {
    "Customer": ["Customer Profile", "Customer Contact Info", "Support Tickets", "Loyalty Rewards", "Address Book"],
    "Financial": ["Credit Card History", "Corporate Tax Filings", "Disputed Invoice Logs", "Wire Transfer Audit", "Bank Account Meta"],
    "Employee": ["Payroll & Bank Details", "Performance Reviews", "Candidate Resumes", "Health Insurance Enrolment", "Timecard Logs"],
    "Identity": ["KYC Documents", "Biometric Pass Hashes", "Passport Scan Copy", "Driver License Scans", "SSN Hash Record"],
    "Transaction": ["Checkout Sessions", "Vendor Invoices", "Clickstream Logs", "API Access Token Logs", "Shipping Waybills"]
}

SENSITIVITY_LEVELS = ["High", "Medium", "Low"]
STATUSES = ["Active", "Expired", "Expiring Soon"]
OWNERS = ["Customer Success Dept", "Marketing Operations", "Support Ops", "Finance Operations", "Legal & Compliance", "HR & Payroll", "Talent Acquisition", "Compliance & Security", "Web Engineering", "Procurement Dept", "InfoSec Engineering"]
SOURCES = ["CRM Database", "Web Signups", "Zendesk Import", "Stripe Billing Vault", "ERP Accounting", "Workday Payroll", "Greenhouse ATS", "Jumio Verification", "Redis Cache Dump", "SAP Procurement", "Segment Telemetry"]

PURPOSES = [
    ("Order Processing & Delivery", "Order Processing & Delivery", False),
    ("Account Management", "Targeted Marketing Campaigns", True),
    ("Customer Support Resolution", "Support Resolution", False),
    ("Payment Billing & Fraud Prevention", "Payment Billing & Fraud Prevention", False),
    ("Tax & Legal Audit Compliance", "Tax Audit", False),
    ("Dispute Resolution", "Product Analytics & Risk Modeling", True),
    ("Salary Disbursement", "Salary Disbursement", False),
    ("Recruitment & Assessment", "AI Resume Screening Training", True),
    ("AML Verification", "AML Verification", False),
    ("Physical Security Access", "Office Security Access", False),
    ("UI Experience Optimization", "Third-Party Data Broker Monetization", True),
]

def generate_records(count=20):
    records = []
    base_date = datetime.now()

    for i in range(1, count + 1):
        cat = random.choice(list(CATEGORIES.keys()))
        data_type = random.choice(CATEGORIES[cat])
        sens = random.choice(SENSITIVITY_LEVELS)
        owner = random.choice(OWNERS)
        source = random.choice(SOURCES)

        purpose_tuple = random.choice(PURPOSES)
        col_purpose, curr_usage, is_mismatch = purpose_tuple

        # Dates & Status
        created_days_ago = random.randint(30, 1000)
        created_dt = base_date - timedelta(days=created_days_ago)

        retention_years = random.choice([1, 2, 3, 5])
        expiry_dt = created_dt + timedelta(days=retention_years * 365)

        days_until_expiry = (expiry_dt - base_date).days

        if days_until_expiry < 0:
            status = "Expired"
        elif days_until_expiry <= 30:
            status = "Expiring Soon"
        else:
            status = "Active"

        prefix_map = {"Customer": "CUS", "Financial": "FIN", "Employee": "EMP", "Identity": "IDN", "Transaction": "TRX"}
        rec_prefix = prefix_map[cat]
        record_id = f"{rec_prefix}-{1000 + i}"

        rec = {
            "record_id": record_id,
            "data_type": data_type,
            "category": cat,
            "sensitivity": sens,
            "collection_purpose": col_purpose,
            "current_usage": curr_usage,
            "owner": owner,
            "created_date": created_dt.strftime("%Y-%m-%d"),
            "retention_period": f"{retention_years} years",
            "expiry_date": expiry_dt.strftime("%Y-%m-%d"),
            "status": status,
            "last_accessed": (base_date - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
            "source": source,
            "purpose_mismatch": is_mismatch,
            "risk_level": "Critical" if is_mismatch and status == "Expired" else ("High" if sens == "High" or is_mismatch else "Medium" if status == "Expired" else "Low"),
            "ai_recommendation": "DELETE" if (status == "Expired" and is_mismatch) else ("ANONYMIZE" if (status == "Expired" and sens == "High") else ("REVIEW" if (status == "Expired" or is_mismatch) else "KEEP")),
            "ai_explanation": f"Automated analysis for {record_id}. Status: {status}, Mismatch: {is_mismatch}.",
            "policy_rule": f"STD-POL-0{retention_years}Y",
            "review_status": "Pending",
            "anonymization_status": "Not Required",
            "deletion_status": "Not Required"
        }
        records.append(rec)

    return records

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic DATAEXPIRY records.")
    parser.add_argument("--count", type=int, default=20, help="Number of records to generate")
    parser.add_argument("--output", type=str, default="data/synthetic/records.json", help="Output JSON file path")
    args = parser.parse_args()

    data = generate_records(args.count)
    with open(args.output, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Successfully generated {args.count} synthetic records into {args.output}")
