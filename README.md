# Banking System API (Ledger-Based Backend)

A simplified banking backend built to practice **backend correctness** and **concurrency-safe** database operations. The system uses a **ledger** (`ledger_transactions`) as an append-only event log and an `accounts` table for current balances. A FastAPI layer exposes the functionality via REST endpoints with Swagger UI.

## Why this project
Most “banking API” demos are CRUD-only. This project focuses on:
- **Atomic operations** (all-or-nothing updates)
- **Concurrency safety** (row-level locking to prevent race conditions)
- **Auditability** (append-only ledger of all events)
- **Deterministic history** (`ORDER BY timestamp, transaction_id`)

---

## Tech stack
- **Python**
- **FastAPI** (OpenAPI/Swagger UI)
- **PostgreSQL**
- **psycopg (v3)**

---

## Project scope (intentional simplifications)
- No account merges
- No account “active/inactive” status
- `account_id` is unique forever (cannot be reused)
- No authentication/authorization (out of scope for this iteration)

---

## Architecture

### Layered design
```
Client (Swagger/curl)
↓ HTTP/JSON
FastAPI (main.py)
↓ method calls
BankingSystemImpl (domain adapter)
↓ delegates
BankingStore (psycopg + SQL transactions/locks)
↓ SQL
PostgreSQL (accounts + ledger_transactions)
```

### Key database tables

- `accounts`: current balance per account
- `ledger_transactions`: append-only log of operations (deposits, transfers, payments, cashbacks)
- `payment_seq`: sequence to generate `paymentN` ids

---

## Database schema

Create a file named `schema.sql` in the project root:

```sql
BEGIN;

DROP TABLE IF EXISTS ledger_transactions CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP SEQUENCE IF EXISTS payment_seq;

CREATE TABLE accounts (
  account_id  TEXT    PRIMARY KEY,
  created_at  BIGINT  NOT NULL,
  balance     BIGINT  NOT NULL DEFAULT 0
);

CREATE TABLE ledger_transactions (
  transaction_id BIGSERIAL PRIMARY KEY,
  account_id     TEXT      NOT NULL REFERENCES accounts(account_id) ON DELETE RESTRICT,
  timestamp      BIGINT    NOT NULL,
  operation      TEXT      NOT NULL,
  amount         BIGINT    NOT NULL,
  payment_ref    TEXT      NULL,
  deposited      BOOLEAN   NULL
);

CREATE SEQUENCE payment_seq START 1;

CREATE INDEX idx_ledger_account_time
  ON ledger_transactions(account_id, timestamp);

CREATE INDEX idx_cashback_due
  ON ledger_transactions(timestamp)
  WHERE operation = 'cashback' AND deposited = FALSE;

COMMIT;

```

---

## Setup 
### 1) Create Database user + Database
From WSL:
```bash
sudo -u postgres psql <<'SQL'
DROP DATABASE IF EXISTS banking_db;
DROP ROLE IF EXISTS bank_user;

CREATE ROLE bank_user WITH LOGIN PASSWORD 'bank_pass';
CREATE DATABASE banking_db OWNER bank_user;
GRANT ALL PRIVILEGES ON DATABASE banking_db TO bank_user;
SQL
```
### 2) Create venv + install dependencies
```bash
make install
```
### 3) Apply Schema
```bash
psql "postgresql://bank_user:bank_pass@127.0.0.1:5432/banking_db" -f schema.sql
```
### Run the API
```bash
make dev
```
Swagger UI:
- https://localhost:8000/docs

---

## Configuration
For local simplicity, `main.py` corrently hard-codes the DSN:
```python
DATABASE_URL = "postgresql://bank_user:bank_pass@127.0.0.1:5432/banking_db"
```
The next iteration of implamentation id to move to cloud. This willbe replased with an envirnment variable.

---

## API Endpoints
### Health
- `GET / health`

### Accounts
- `POST / accounts` -- create account
- `GET / accounts` -- list account IDs
- `GET / {account_id/balance}` -- currenct balance for a specified account

### Money Movement
- `POST / deposits` -- add money to account
- `POST / transfers` -- transfer money between accounts
- `POST / payments` -- make payments that apply cashback deposits

### Legder
- `GET /accounts/{account_id}/transactions?timestamp=<ms>` -- all ledger entires for a specified account

