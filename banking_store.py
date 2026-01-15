from __future__ import annotations

from dataclasses import dataclass
import psycopg
from psycopg.rows import dict_row

MILLISECONDS_IN_1_DAY = 86_400_000


@dataclass(frozen=True)
class Account:
    account_id: str
    created_at: int
    balance: int


class BankingStore:
    """
    PostgreSQL-backed store.

    Design (simplified):
      - No merges
      - No versions
      - account_id is unique forever (cannot be reused)
      - One row per account in `accounts`
      - Append-only history + delayed cashback in `ledger_transactions`

    All write operations:
      - BEGIN
      - process cashbacks
      - SELECT ... FOR UPDATE (locks)
      - update balances + insert ledger rows
      - COMMIT
    """

    def __init__(self, dsn: str):
        self.dsn = dsn

    # ---------- helpers ----------

    def _get_account_for_update(self, cur, account_id: str) -> Account | None:
        cur.execute(
            """
            SELECT account_id, created_at, balance
            FROM accounts
            WHERE account_id = %s
            FOR UPDATE
            """,
            (account_id,),
        )
        row = cur.fetchone()
        return None if row is None else Account(**row)

    def _process_cashbacks(self, cur, timestamp: int) -> None:
        """
        Apply due cashbacks (timestamp <= now) exactly once.
        Uses row locks to make it safe under concurrency.
        """
        cur.execute(
            """
            SELECT transaction_id, account_id, amount
            FROM ledger_transactions
            WHERE operation = 'cashback'
              AND timestamp <= %s
              AND deposited = FALSE
            FOR UPDATE
            """,
            (timestamp,),
        )
        due = cur.fetchall()

        for r in due:
            # Credit the account
            cur.execute(
                """
                UPDATE accounts
                SET balance = balance + %s
                WHERE account_id = %s
                """,
                (r["amount"], r["account_id"]),
            )
            # Mark cashback as deposited (idempotency)
            cur.execute(
                """
                UPDATE ledger_transactions
                SET deposited = TRUE
                WHERE transaction_id = %s
                """,
                (r["transaction_id"],),
            )

    # ---------- API methods ----------

    def create_account(self, timestamp: int, account_id: str) -> bool:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("BEGIN")

                # account_id cannot be reused
                cur.execute("SELECT 1 FROM accounts WHERE account_id = %s", (account_id,))
                if cur.fetchone() is not None:
                    cur.execute("ROLLBACK")
                    return False

                cur.execute(
                    """
                    INSERT INTO accounts(account_id, created_at, balance)
                    VALUES (%s, %s, 0)
                    """,
                    (account_id, timestamp),
                )

                cur.execute(
                    """
                    INSERT INTO ledger_transactions(account_id, timestamp, operation, amount)
                    VALUES (%s, %s, 'created', 0)
                    """,
                    (account_id, timestamp),
                )

                cur.execute("COMMIT")
                return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("BEGIN")
                self._process_cashbacks(cur, timestamp)

                acct = self._get_account_for_update(cur, account_id)
                if acct is None:
                    cur.execute("ROLLBACK")
                    return None

                cur.execute(
                    """
                    INSERT INTO ledger_transactions(account_id, timestamp, operation, amount)
                    VALUES (%s, %s, 'deposited', %s)
                    """,
                    (account_id, timestamp, amount),
                )

                cur.execute(
                    """
                    UPDATE accounts
                    SET balance = balance + %s
                    WHERE account_id = %s
                    RETURNING balance
                    """,
                    (amount, account_id),
                )
                new_balance = cur.fetchone()["balance"]

                cur.execute("COMMIT")
                return new_balance

    def get_accounts(self) -> list[str]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT account_id FROM accounts ORDER BY account_id")
                return [r["account_id"] for r in cur.fetchall()]

    def get_balance(self, account_id: str) -> int | None:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT balance FROM accounts WHERE account_id = %s",
                    (account_id,),
                )
                row = cur.fetchone()
                return None if row is None else row["balance"]

    def transfer(self, timestamp: int, source: str, target: str, amount: int) -> int | None:
        if source == target:
            return None

        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("BEGIN")
                self._process_cashbacks(cur, timestamp)

                # Deadlock-safe locking order
                first, second = sorted([source, target])

                acct_first = self._get_account_for_update(cur, first)
                acct_second = self._get_account_for_update(cur, second)

                if acct_first is None or acct_second is None:
                    cur.execute("ROLLBACK")
                    return None

                # Map back to source/target
                acct_src = acct_first if acct_first.account_id == source else acct_second
                acct_dst = acct_second if acct_first.account_id == source else acct_first

                if acct_src.balance < amount:
                    cur.execute("ROLLBACK")
                    return None

                # Ledger rows
                cur.execute(
                    """
                    INSERT INTO ledger_transactions(account_id, timestamp, operation, amount)
                    VALUES (%s, %s, 'transferred out', %s)
                    """,
                    (acct_src.account_id, timestamp, amount),
                )
                cur.execute(
                    """
                    INSERT INTO ledger_transactions(account_id, timestamp, operation, amount)
                    VALUES (%s, %s, 'transferred in', %s)
                    """,
                    (acct_dst.account_id, timestamp, amount),
                )

                # Balances
                cur.execute(
                    """
                    UPDATE accounts
                    SET balance = balance - %s
                    WHERE account_id = %s
                    """,
                    (amount, acct_src.account_id),
                )
                cur.execute(
                    """
                    UPDATE accounts
                    SET balance = balance + %s
                    WHERE account_id = %s
                    """,
                    (amount, acct_dst.account_id),
                )

                # Return source balance
                cur.execute(
                    "SELECT balance FROM accounts WHERE account_id = %s",
                    (acct_src.account_id,),
                )
                src_balance = cur.fetchone()["balance"]

                cur.execute("COMMIT")
                return src_balance

    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("BEGIN")
                self._process_cashbacks(cur, timestamp)

                acct = self._get_account_for_update(cur, account_id)
                if acct is None or acct.balance < amount:
                    cur.execute("ROLLBACK")
                    return None

                cur.execute("SELECT nextval('payment_seq') AS n")
                payment_id = f"payment{cur.fetchone()['n']}"

                # Deduct now
                cur.execute(
                    """
                    UPDATE accounts
                    SET balance = balance - %s
                    WHERE account_id = %s
                    """,
                    (amount, account_id),
                )

                # Payment ledger row
                cur.execute(
                    """
                    INSERT INTO ledger_transactions(account_id, timestamp, operation, amount)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (account_id, timestamp, payment_id, amount),
                )

                # Schedule cashback (+1 day, 2%)
                cashback_amount = int(amount * 0.02)
                cashback_timestamp = timestamp + MILLISECONDS_IN_1_DAY
                cur.execute(
                    """
                    INSERT INTO ledger_transactions(
                      account_id, timestamp, operation, amount, payment_ref, deposited
                    )
                    VALUES (%s, %s, 'cashback', %s, %s, FALSE)
                    """,
                    (account_id, cashback_timestamp, cashback_amount, payment_id),
                )

                cur.execute("COMMIT")
                return payment_id
