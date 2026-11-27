---
status: accepted
---

# Run on an Oracle free server with AWS storage

Airflow, FastAPI and MLflow run on a separate Oracle Cloud Always Free server (1 CPU, 6 GB), while clean data lives in a new database on an existing AWS RDS PostgreSQL instance and raw FPL responses in a new S3 bucket. The frontend is on Vercel. The site and API share one bought domain so that session cookies work.

## Considered Options

- **Everything on AWS**: simpler networking, but compute would exceed the budget.
- **Sharing the existing app's Oracle server**: no new server, but one app could take down the other.
- **A new RDS instance**: about US$12–15 a month on its own.

## Consequences

- RDS must accept connections from the Oracle server: limited to its IP, with SSL required, and a public IPv4 address at about US$3.60 a month.
- Airflow's own metadata database runs on the Oracle server, not on RDS.
- Oracle's free allowance is shared across the account and its servers may be reclaimed if idle; this stack's memory use keeps it above the idle threshold.
