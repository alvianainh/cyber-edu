from pydantic import BaseModel, EmailStr

class RegisterModel(BaseModel):
    email: str
    password: str
    full_name: str

class LoginModel(BaseModel):
    email: str
    password: str
