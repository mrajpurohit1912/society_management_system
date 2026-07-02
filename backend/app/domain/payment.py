from dataclasses import Field

from pydantic import BaseModel
from uuid import uuid4


class Payment(BaseModel):
    id:str = Field(default_factory=lambda: str(uuid4()))