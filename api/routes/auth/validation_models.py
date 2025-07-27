from pydantic import BaseModel, Field, EmailStr

class RegisterModel(BaseModel):
    username: str = Field(min_length=2, max_length=16)
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)

class LoginModel(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)