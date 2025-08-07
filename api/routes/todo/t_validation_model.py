from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from typing import Optional

class TodoCreationModel(BaseModel):
    title: str = Field(min_length=2, max_length=140)
    description: str = Field(min_length=0, max_length=320)

class TodoDeletionModel(BaseModel):
    todo_id: UUID

class TodoEditorModel(TodoCreationModel):
    todo_id: UUID

class TodoExistCheckModel(BaseModel):
    user_id: UUID
    title: Optional[str] = None
    todo_id: Optional[UUID] = None

    @model_validator(mode="before")
    @classmethod
    def validate_title_or_todoID(cls, data: dict) -> dict:
        if not data.get("title") and not data.get("todo_id"):
            raise ValueError("Either title or todo_id must be provided.")
        return data
    
RunTodoDbStatementModel = TodoExistCheckModel