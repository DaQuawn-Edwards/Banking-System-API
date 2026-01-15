from abc import ABC


class BankingSystem(ABC):
    """
    `BankingSystem` interface.
    """

    def create_account(self, timestamp: int, account_id: str) -> bool:
        """
        Should create a new account with the given identifier if it
        doesn't already exist.
        Returns `True` if the account was successfully created or
        `False` if an account with `account_id` already exists.
        """
        # default implementation
        return False

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        """
        Should deposit the given `amount` of money to the specified
        account `account_id`.
        Returns the balance of the account after the operation has
        been processed.
        If the specified account doesn't exist, should return
        `None`.
        """
        # default implementation
        return None

    def transfer(self, timestamp: int, source_account_id: str, target_account_id: str, amount: int) -> int | None:
        """
        Should transfer the given amount of money from account
        `source_account_id` to account `target_account_id`.
        Returns the balance of `source_account_id` if the transfer
        was successful or `None` otherwise.
          * Returns `None` if `source_account_id` or
          `target_account_id` doesn't exist.
          * Returns `None` if `source_account_id` and
          `target_account_id` are the same.
          * Returns `None` if account `source_account_id` has
          insufficient funds to perform the transfer.
        """
        # default implementation
        return None

    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        """
        Should return the identifiers of the top `n` accounts with
        the highest outgoing transactions - the total amount of
        money either transferred out of or paid/withdrawn (the
        **pay** operation will be introduced in level 3) - sorted in
        descending order, or in case of a tie, sorted alphabetically
        by `account_id` in ascending order.
        The result should be a list of strings in the following
        format: `["<account_id_1>(<total_outgoing_1>)", "<account_id
        _2>(<total_outgoing_2>)", ..., "<account_id_n>(<total_outgoi
        ng_n>)"]`.
          * If less than `n` accounts exist in the system, then return
          all their identifiers (in the described format).
          * Cashback (an operation that will be introduced in level 3)
          should not be reflected in the calculations for total
          outgoing transactions.
        """
        # default implementation
        return []

    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        """
        Should withdraw the given amount of money from the specified
        account.
        All withdraw transactions provide a 2% cashback - 2% of the
        withdrawn amount (rounded down to the nearest integer) will
        be refunded to the account 24 hours after the withdrawal.
        If the withdrawal is successful (i.e., the account holds
        sufficient funds to withdraw the given amount), returns a
        string with a unique identifier for the payment transaction
        in this format:
        `"payment[ordinal number of withdraws from all accounts]"` -
        e.g., `"payment1"`, `"payment2"`, etc.
        Additional conditions:
          * Returns `None` if `account_id` doesn't exist.
          * Returns `None` if `account_id` has insufficient funds to
          perform the payment.
          * **top_spenders** should now also account for the total
          amount of money withdrawn from accounts.
          * The waiting period for cashback is 24 hours, equal to
          `24 * 60 * 60 * 1000 = 86400000` milliseconds (the unit for
          timestamps).
          So, cashback will be processed at timestamp
          `timestamp + 86400000`.
          * When it's time to process cashback for a withdrawal, the
          amount must be refunded to the account before any other
          transactions are performed at the relevant timestamp.
        """
        # default implementation
        return None

    def get_payment_status(self, timestamp: int, account_id: str, payment: str) -> str | None:
        """
        Should return the status of the payment transaction for the
        given `payment`.
        Specifically:
          * Returns `None` if `account_id` doesn't exist.
          * Returns `None` if the given `payment` doesn't exist for
          the specified account.
          * Returns `None` if the payment transaction was for an
          account with a different identifier from `account_id`.
          * Returns a string representing the payment status:
          `"IN_PROGRESS"` or `"CASHBACK_RECEIVED"`.
        """
        # default implementation
        return None

    def merge_accounts(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool:
        """
        Should merge `account_id_2` into the `account_id_1`.
        Returns `True` if accounts were successfully merged, or
        `False` otherwise.
        Specifically:
          * Returns `False` if `account_id_1` is equal to
          `account_id_2`.
          * Returns `False` if `account_id_1` or `account_id_2`
          doesn't exist.
          * All pending cashback refunds for `account_id_2` should
          still be processed, but refunded to `account_id_1` instead.
          * After the merge, it must be possible to check the status
          of payment transactions for `account_id_2` with payment
          identifiers by replacing `account_id_2` with `account_id_1`.
          * The balance of `account_id_2` should be added to the
          balance for `account_id_1`.
          * `top_spenders` operations should recognize merged accounts
          - the total outgoing transactions for merged accounts should
          be the sum of all money transferred and/or withdrawn in both
          accounts.
          * `account_id_2` should be removed from the system after the
          merge.
        """
        # default implementation
        return False

    def get_balance(self, timestamp: int, account_id: str, time_at: int) -> int | None:
        """
        Should return the total amount of money in the account
        `account_id` at the given timestamp `time_at`.
        If the specified account did not exist at a given time
        `time_at`, returns `None`.
          * If queries have been processed at timestamp `time_at`,
          `get_balance` must reflect the account balance **after** the
          query has been processed.
          * If the account was merged into another account, the merged
          account should inherit its balance history.
        """
        # default implementation
        return None
