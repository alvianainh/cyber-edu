from pydantic import BaseModel

class RegisterModel(BaseModel):
    email: str
    password: str
    full_name: str

class LoginModel(BaseModel):
    email: str
    password: str