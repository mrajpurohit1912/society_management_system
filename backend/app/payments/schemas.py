import uuid
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class PaymentDomain(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    amount: float
    status: str
    description: Optional[str] = None

