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
