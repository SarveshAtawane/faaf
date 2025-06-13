from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    name: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
