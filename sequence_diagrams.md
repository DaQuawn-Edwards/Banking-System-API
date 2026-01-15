# Create account
sequenceDiagram
  autonumber
  actor Client
  participant API as FastAPI (main.py)
  participant Domain as BankingSystemImpl
  participant Store as BankingStore (psycopg)
  participant DB as PostgreSQL

  Client->>API: POST /accounts {timestamp, account_id}
  API->>Domain: create_account(timestamp, account_id)
  Domain->>Store: create_account(timestamp, account_id)
  Store->>DB: BEGIN
  Store->>DB: SELECT 1 FROM accounts WHERE account_id=?
  alt account exists
    Store->>DB: ROLLBACK
    Store-->>Domain: False
    Domain-->>API: False
    API-->>Client: 409 Conflict
  else account does not exist
    Store->>DB: INSERT INTO accounts(account_id, created_at, balance=0)
    Store->>DB: INSERT INTO ledger_transactions(... operation='created')
    Store->>DB: COMMIT
    Store-->>Domain: True
    Domain-->>API: True
    API-->>Client: 201 Created
  end
