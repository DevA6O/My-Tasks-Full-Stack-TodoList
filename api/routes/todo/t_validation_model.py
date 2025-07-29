from uuid import UUID
from pydantic import BaseModel, Field

class TodoCreation(BaseModel):
    user_id: UUID
    title: str = Field(min_length=2, max_length=140)
    description: str = Field(min_length=0, max_length=320)