"""Validated contracts for opportunities and follow-up work."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal
from pydantic import Field, field_validator, model_validator
from .schemas import StrictModel, Record

Stage = Literal['lead','qualified','proposal','won','lost']
TaskStatus = Literal['open','in_progress','done']

class Links(StrictModel):
    company_id: str | None = Field(None, min_length=1, max_length=100)
    contact_id: str | None = Field(None, min_length=1, max_length=100)

class DealInput(Links):
    title: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(default=Decimal('0'), ge=0, max_digits=14, decimal_places=2)
    currency: str = Field(default='USD', pattern=r'^[A-Z]{3}$')
    stage: Stage = 'lead'
    expected_close_date: date | None = None
    notes: str | None = Field(None, max_length=5000)

class TaskInput(Links):
    title: str = Field(min_length=1, max_length=200)
    due_date: date | None = None
    status: TaskStatus = 'open'
    deal_id: str | None = Field(None, min_length=1, max_length=100)
    notes: str | None = Field(None, max_length=5000)

class ActivityInput(Links):
    type: Literal['note','call','meeting','email'] = 'note'
    occurred_at: datetime
    note: str = Field(min_length=1, max_length=5000)
    deal_id: str | None = Field(None, min_length=1, max_length=100)

    @field_validator('occurred_at')
    @classmethod
    def aware_time(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('Include a timezone in occurred_at.')
        return value.astimezone(timezone.utc)

    @model_validator(mode='after')
    def linked(self):
        if not (self.company_id or self.contact_id or self.deal_id):
            raise ValueError('Link an activity to a company, contact, or deal.')
        return self

class DealOutput(DealInput, Record):
    pass
class TaskOutput(TaskInput, Record):
    pass
class ActivityOutput(ActivityInput, Record):
    pass

class DealPage(StrictModel):
    items: list[DealOutput]
    total: int
    limit: int
    offset: int
class TaskPage(StrictModel):
    items: list[TaskOutput]
    total: int
    limit: int
    offset: int
class ActivityPage(StrictModel):
    items: list[ActivityOutput]
    total: int
    limit: int
    offset: int
