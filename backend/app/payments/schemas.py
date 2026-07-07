import uuid
from typing import Optional
from pydantic import BaseModel, Field

class PaymentDomain(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    amount: float
    status: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
