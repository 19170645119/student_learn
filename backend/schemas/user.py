from pydantic import BaseModel, Field, EmailStr, model_validator
from typing import Annotated

UsernameStr = Annotated[str, Field(..., min_length=2, max_length=20)]
RawPasswordStr = Annotated[str, Field(min_length=6, max_length=20)]

class RegisterIn(BaseModel):
    email: EmailStr
    username: UsernameStr
    password: RawPasswordStr
    confirm_password: RawPasswordStr
    code: Annotated[str, Field(..., min_length=4, max_length=4)]

    @model_validator(mode="after")
    def password_is_match(self) -> "RegisterIn":
        if self.password != self.confirm_password:
            raise ValueError("密码不一致")
        return self

class UserCreateSchema(BaseModel):
    email: EmailStr
    password: RawPasswordStr
    username: UsernameStr

class LoginIn(BaseModel):
    email: EmailStr
    password: RawPasswordStr

class UserSchema(BaseModel):
    id: int
    email: str
    username: str

    class Config:
        from_attributes = True

class LoginOut(BaseModel):
    user: UserSchema
    token: str
