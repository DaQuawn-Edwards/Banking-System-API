from banking_system import BankingSystem
from banking_store import BankingStore

class BankingSystemImpl(BankingSystem):
    def __init__(self, dsn: str) -> None:
        self.store = BankingStore(dsn)

    def create_account(self, timestamp, account_id) -> bool:
        return self.store.create_account(timestamp, account_id)
    
    def get_accounts(self) -> list[str]:
        return self.store.get_accounts()

    def get_balance(self, account_id: str) -> int | None:
        return self.store.get_balance(account_id)

    def deposit(self, timestamp, account_id, amount):
        return self.store.deposit(timestamp, account_id, amount)

    def transfer(self, timestamp, source_account_id, target_account_id, amount):
        return self.store.transfer(timestamp, source_account_id, target_account_id, amount)

    def pay(self, timestamp, account_id, amount):
        return self.store.pay(timestamp, account_id, amount)
    
    def get_transactions(self, timestamp:int, account_id: str):
        return self.store.get_transactions(timestamp, account_id)
