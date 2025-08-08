from uuid import UUID
from fastapi import status
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional, Type, Any

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
    

class HandleTodoRequestModel(BaseModel):
    """
        Args:
            token (str): Bearer token
            service_class (Any): The service class to instantiate (e.g., TodoEditor)
            service_method (str): The method name to call (e.g. "update", "delete", ...)
            default_error_message (str): The default error message which should be returned if an error occurred
            http_status_success (int): The success status_code. Default is 200 (OK).
            http_status_exception (int): The exception status_code. Default is 400 (BAD REQUEST).
    """

    token: str = Field(..., min_length=10)
    service_class: Type[Any]
    service_method: str
    default_error_message: str
    http_status_success: int = status.HTTP_200_OK
    http_status_exception: int = status.HTTP_400_BAD_REQUEST

    @field_validator("http_status_success", "http_status_exception")
    @classmethod
    def validate_http_status(cls, value) -> int:
        if not (100 <= value <= 599):
            raise ValueError("Invalid HTTP status code.")
        return value
    
    @field_validator("service_method")
    @classmethod
    def validate_service_method(cls, value: str) -> str:
        if not value.isidentifier():
            raise ValueError("Service method is not a valid Python identifier.")
        return value
    
    @model_validator(mode="after")
    def check_method_exists(self) -> 'HandleTodoRequestModel':
        if not hasattr(self.service_class, self.service_method):
            raise ValueError(f"'{self.service_class.__name__}' has no method '{self.service_method}'")
        return self