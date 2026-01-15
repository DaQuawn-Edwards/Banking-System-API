from __future__ import annotations
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from banking_system_impl import BankingSystemImpl

# -------------------------------------------------
# App setup
# -------------------------------------------------

DATABASE_URL = "postgresql://bank_user:bank_pass@127.0.0.1:5432/banking_db"

bank = BankingSystemImpl(DATABASE_URL)

app = FastAPI(
    title="Banking API",
    description="PostgreSQL-backed banking ledger with delayed cashback",
    version="0.1.0",
)

# -------------------------------------------------
# Request / Response models
# -------------------------------------------------

class CreateAccountRequest(BaseModel):
    timestamp: int = Field(..., description="Milliseconds since epoch")
    account_id: str = Field(..., min_length=1)


class DepositRequest(BaseModel):
    timestamp: int
    account_id: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0)


class TransferRequest(BaseModel):
    timestamp: int
    source_account_id: str = Field(..., min_length=1)
    target_account_id: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0)


class PayRequest(BaseModel):
    timestamp: int
    account_id: str = Field(..., min_length=1)
    amount: int = Field(..., gt=0)


class BalanceResponse(BaseModel):
    balance: int


class PaymentResponse(BaseModel):
    payment_id: str

class Transaction(BaseModel):
    transaction_id: int
    timestamp: int
    operation: str
    amount: int
    payment_ref: Optional[str] = None
    deposited: Optional[bool] = None

class TransactionResponse(BaseModel):
    account_id: str
    transactions: List[Transaction]


# -------------------------------------------------
# Routes
# -------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/accounts", status_code=201)
def create_account(request: CreateAccountRequest):
    created = bank.create_account(request.timestamp, request.account_id)
    if not created:
        raise HTTPException(
            status_code=409,
            detail="Account already exists",
        )
    return {"account_id": request.account_id, "created": True}


@app.post("/deposits", response_model=BalanceResponse)
def deposit(request: DepositRequest):
    balance = bank.deposit(request.timestamp, request.account_id, request.amount)
    if balance is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )
    return BalanceResponse(balance=balance)


@app.get("/accounts")
def get_accounts():
    return {"accounts": bank.get_accounts()}


@app.get("/accounts/{account_id}/balance")
def get_balance(account_id: str):
    balance = bank.get_balance(account_id)
    if balance is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )
    return {"account_id": account_id, "balance": balance}


@app.post("/transfers", response_model=BalanceResponse)
def transfer(request: TransferRequest):
    balance = bank.transfer(
        request.timestamp,
        request.source_account_id,
        request.target_account_id,
        request.amount,
    )
    if balance is None:
        raise HTTPException(
            status_code=400,
            detail="Transfer failed",
        )
    return BalanceResponse(balance=balance)


@app.post("/payments", response_model=PaymentResponse)
def pay(request: PayRequest):
    payment_id = bank.pay(request.timestamp, request.account_id, request.amount)
    if payment_id is None:
        raise HTTPException(
            status_code=400,
            detail="Payment failed",
        )
    return PaymentResponse(payment_id=payment_id)

@app.get("/accounts/{account_id}/transactions", response_model=TransactionResponse)
def get_transactions(timestamp:int, account_id: str):
    txns = bank.get_transactions(timestamp, account_id)
    if txns is None:
        raise HTTPException(
            status_code=404,
            detail= "account not found"
        )
    
    return TransactionResponse(
        account_id=account_id,
        transactions=txns
    )