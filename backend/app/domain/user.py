from pydantic import BaseModel,Field
from uuid import uuid4


class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: str = Field(max_length=100)
    password: str = Field(max_length=50)
    phone_number: str = Field(max_length=10)


    