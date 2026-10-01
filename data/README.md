# Synthetic Data Infrastructure

This folder contains synthetic datasets and seed scripts for local development and testing of the DATAEXPIRY platform.

## Dataset Location

- `synthetic/records.json`: Initial synthetic dataset containing 20+ records spanning diverse categories, sensitivity levels, and lifecycle statuses.
- `synthetic/generator.py`: Synthetic data generator script for generating 100–200+ additional records on demand.

## Synthetic Categories Covered

1. **Customer**: Customer profile details, order histories, interaction logs.
2. **Financial**: Bank account numbers, payment transactions, credit scores, tax documents.
3. **Employee**: Payroll records, performance evaluations, employee contracts.
4. **Identity**: Government IDs, passport numbers, biometric metadata hashes.
5. **Transaction**: E-commerce purchases, refund logs, audit traces.

## How to Seed the Database

From the project root:

```bash
cd backend
python seed_db.py
```

## How to Generate More Data (100–200+ records)

To scale up testing data for performance benchmarks or pagination testing:

```bash
python data/synthetic/generator.py --count 100 --output data/synthetic/records_large.json
```
