"""Typed source contracts. All money is integer USD cents; timestamps are UTC-naive."""

from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Account(Record):
    account_id: str
    signup_date: date
    segment: Literal["SMB", "Mid-market", "Enterprise"]
    region: Literal["AMER", "EMEA", "APAC"]
    channel: Literal["organic", "paid_search", "partner", "content"]


class User(Record):
    user_id: str
    account_id: str
    created_date: date


class Subscription(Record):
    account_id: str
    month: date
    amount_cents: int = Field(ge=0)
    billing_period: Literal["monthly", "annual"]
    plan: Literal["Starter", "Growth", "Scale"]


class Event(Record):
    event_id: str
    user_id: str
    account_id: str
    occurred_at: datetime
    event_name: Literal["login", "workspace_created", "invite_sent", "report_created", "export", "automation"]
    ingested_at: datetime

    @field_validator("occurred_at", "ingested_at")
    @classmethod
    def utc_timestamp(cls, value):
        # Offset-aware feeds are normalized before storage; naive source values mean UTC.
        return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


class Opportunity(Record):
    account_id: str
    trial_date: date
    qualified_date: date | None
    paid_date: date | None


class Spend(Record):
    spend_date: date
    channel: Literal["organic", "paid_search", "partner", "content"]
    spend_cents: int = Field(ge=0)


CONTRACTS = {
    "accounts": Account,
    "users": User,
    "subscriptions": Subscription,
    "events": Event,
    "opportunities": Opportunity,
    "marketing": Spend,
}
KEYS = {
    "accounts": ["account_id"],
    "users": ["user_id"],
    "subscriptions": ["account_id", "month"],
    "events": ["event_id"],
    "opportunities": ["account_id"],
    "marketing": ["spend_date", "channel"],
}
