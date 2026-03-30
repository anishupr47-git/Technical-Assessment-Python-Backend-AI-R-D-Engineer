from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomerOut(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ActivityOut(BaseModel):
    id: int
    customer_id: int
    type: str
    title: str
    content: str
    source: str
    created_at: datetime
    ai_summary: str | None = None
    ai_category: str | None = None
    ai_priority: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SyncSummary(BaseModel):
    customers_fetched: int
    customers_inserted: int
    customers_skipped: int
    activities_fetched: int
    activities_inserted: int
    activities_skipped: int
    activities_missing_customer: int
    errors: list[str]