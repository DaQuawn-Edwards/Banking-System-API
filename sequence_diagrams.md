# POST endpoints
## Create account (POST / accounts)

```mermaid
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
```
## Deposit (POST / deposits)

```mermaid
sequenceDiagram
  autonumber
  actor Client
  participant API as FastAPI (main.py)
  participant Domain as BankingSystemImpl
  participant Store as BankingStore (psycopg)
  participant DB as PostgreSQL

  Client->>API: POST /deposits {timestamp, account_id, amount}
  API->>Domain: deposit(timestamp, account_id, amount)
  Domain->>Store: deposit(timestamp, account_id, amount)

  Store->>DB: BEGIN
  Store->>DB: SELECT due cashbacks FOR UPDATE
  loop for each due cashback
    Store->>DB: UPDATE accounts SET balance=balance+cashback
    Store->>DB: UPDATE ledger_transactions SET deposited=TRUE
  end

  Store->>DB: SELECT account row FOR UPDATE
  alt account missing
    Store->>DB: ROLLBACK
    Store-->>Domain: None
    Domain-->>API: None
    API-->>Client: 404 Not Found
  else account exists
    Store->>DB: INSERT ledger_transactions (operation='deposited')
    Store->>DB: UPDATE accounts SET balance=balance+amount RETURNING balance
    Store->>DB: COMMIT
    Store-->>Domain: new_balance
    Domain-->>API: new_balance
    API-->>Client: 200 OK {balance}
  end
```
## Transfer (POST / transfers)

```mermaid
sequenceDiagram
  autonumber
  actor Client
  participant API as FastAPI (main.py)
  participant Domain as BankingSystemImpl
  participant Store as BankingStore (psycopg)
  participant DB as PostgreSQL

  Client->>API: POST /transfers {timestamp, source, target, amount}
  API->>Domain: transfer(timestamp, source, target, amount)
  Domain->>Store: transfer(timestamp, source, target, amount)

  alt source == target
    Store-->>Domain: None
    Domain-->>API: None
    API-->>Client: 400 Bad Request
  else
    Store->>DB: BEGIN
    Store->>DB: SELECT due cashbacks FOR UPDATE
    loop for each due cashback
      Store->>DB: UPDATE accounts balance
      Store->>DB: Mark cashback deposited
    end

    Note over Store: Lock accounts in sorted order to avoid deadlocks
    Store->>DB: SELECT account(min(source,target)) FOR UPDATE
    Store->>DB: SELECT account(max(source,target)) FOR UPDATE

    alt either account missing
      Store->>DB: ROLLBACK
      Store-->>Domain: None
      Domain-->>API: None
      API-->>Client: 400/404 (your choice)
    else both exist
      Store->>DB: Check source balance >= amount
      alt insufficient funds
        Store->>DB: ROLLBACK
        Store-->>Domain: None
        Domain-->>API: None
        API-->>Client: 400 Bad Request
      else sufficient
        Store->>DB: INSERT ledger (source 'transferred out')
        Store->>DB: INSERT ledger (target 'transferred in')
        Store->>DB: UPDATE accounts SET balance=balance-amount (source)
        Store->>DB: UPDATE accounts SET balance=balance+amount (target)
        Store->>DB: SELECT source balance
        Store->>DB: COMMIT
        Store-->>Domain: source_balance
        Domain-->>API: source_balance
        API-->>Client: 200 OK {balance}
      end
    end
  end
```
## Pay (POST / payments)

```mermaid
sequenceDiagram
  autonumber
  actor Client
  participant API as FastAPI (main.py)
  participant Domain as BankingSystemImpl
  participant Store as BankingStore (psycopg)
  participant DB as PostgreSQL

  Client->>API: POST /payments {timestamp, account_id, amount}
  API->>Domain: pay(timestamp, account_id, amount)
  Domain->>Store: pay(timestamp, account_id, amount)

  Store->>DB: BEGIN
  Store->>DB: SELECT due cashbacks FOR UPDATE
  loop for each due cashback
    Store->>DB: UPDATE accounts balance (+cashback)
    Store->>DB: UPDATE ledger_transactions deposited=TRUE
  end

  Store->>DB: SELECT account FOR UPDATE
  alt account missing or insufficient funds
    Store->>DB: ROLLBACK
    Store-->>Domain: None
    Domain-->>API: None
    API-->>Client: 400 Bad Request
  else ok
    Store->>DB: SELECT nextval('payment_seq')
    Store->>DB: UPDATE accounts SET balance=balance-amount
    Store->>DB: INSERT ledger (operation='paymentN')
    Note over Store: Schedule cashback at timestamp + 86,400,000 ms
    Store->>DB: INSERT ledger (operation='cashback', deposited=FALSE, payment_ref='paymentN')
    Store->>DB: COMMIT
    Store-->>Domain: paymentN
    Domain-->>API: paymentN
    API-->>Client: 200 OK {payment_id}
  end
```

# GET endpoints
## Get accounts (GET / accounts)

```mermaid
sequenceDiagram
  autonumber
  actor Client
  participant API as FastAPI
  participant Domain as BankingSystemImpl
  participant Store as BankingStore
  participant DB as PostgreSQL

  Client->>API: GET /accounts
  API->>Domain: get_accounts()
  Domain->>Store: get_accounts()
  Store->>DB: SELECT account_id FROM accounts ORDER BY account_id
  DB-->>Store: rows
  Store-->>Domain: [account_id...]
  Domain-->>API: list
  API-->>Client: 200 OK {accounts:[...]}
```

## Get balance (GET / accounts / {id} / balance)

```mermaid
sequenceDiagram
  autonumber
  actor Client
  participant API as FastAPI
  participant Domain as BankingSystemImpl
  participant Store as BankingStore
  participant DB as PostgreSQL

  Client->>API: GET /accounts/{account_id}/balance
  API->>Domain: get_balance(account_id)
  Domain->>Store: get_balance(account_id)
  Store->>DB: SELECT balance FROM accounts WHERE account_id=?
  alt not found
    Store-->>Domain: None
    Domain-->>API: None
    API-->>Client: 404 Not Found
  else found
    DB-->>Store: balance
    Store-->>Domain: balance
    Domain-->>API: balance
    API-->>Client: 200 OK {account_id, balance}
  end
```