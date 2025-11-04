from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class BankBase(BaseModel):

    name: str
    code: str
    bin: str
    short_name: str


class Bank(BankBase):
    id: int
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    updated_at: datetime = Field(default=datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class AccountBase(BaseModel):
    email: str
    account_number: int
    account_name: str
    balance: float = 0.00
    currency: str = "VND"
    bank_id: int


class AccountCreate(AccountBase):
    pass


class Account(AccountBase):
    id: int
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    updated_at: datetime = Field(default=datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float
    currency: str = "VND"
    type: str
    status: str = "completed"
    description: str


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: int
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    updated_at: datetime = Field(default=datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class SavedRecipientBase(BaseModel):
    owner_account_id: Optional[int] = None
    account_number: int
    account_name: str
    bank_id: Optional[int]


class SavedRecipientCreate(SavedRecipientBase):
    pass


class SavedRecipient(SavedRecipientBase):
    id: int
    bank_name: Optional[str]
    created_at: datetime = Field(default=datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
