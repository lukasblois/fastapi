from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional, Annotated
from html import escape
from zxcvbn import zxcvbn
from app import utils


class UserCreate(BaseModel):
    email: EmailStr = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        return v.strip().lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v, info):
        if 'email' in info.data:
            result = zxcvbn(v, user_inputs=[info.data['email']])
        else:
            result = zxcvbn(v)

        score = result['score']
        feedback = result['feedback']

        if score < 3:
            suggestions = feedback.get('suggestions', [])
            warning = feedback.get('warning', '')

            error_msg = "Password is too weak. "
            if warning:
                error_msg += f"{warning} "
            if suggestions:
                error_msg += " ".join(suggestions)

            raise ValueError(error_msg)

        return v.strip()


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime  # Added created_at field

    model_config = ConfigDict(from_attributes=True)


class PasswordStrengthResponse(BaseModel):
    is_strong: bool
    score: int
    max_score: int
    crack_time: str
    message: str


class UserLogin(BaseModel):
    email: EmailStr = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        return v.strip().lower()

    @field_validator('password')
    @classmethod
    def sanitize_password(cls, v):
        return v.strip()


class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    published: bool = True

    @field_validator('title', 'content')
    @classmethod
    def sanitize_content(cls, v):
        return escape(v.strip())


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int
    created_at: datetime
    owner_id: int
    owner: UserOut

    model_config = ConfigDict(from_attributes=True)


class PostOut(BaseModel):
    Post: Post
    votes: int

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None


class Vote(BaseModel):
    post_id: int
    dir: Annotated[int, Field(ge=0, le=1)]


class PasswordCheckRequest(BaseModel):
    email: str
    password: str


class PasswordResetInApp(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v, info):
        password = v.strip()

        results = zxcvbn(password)
        if results['score'] < 3:
            feedback = results['feedback'].get('suggestions', [])
            warning = results['feedback'].get('warning', '')
            error_msg = "New password is too weak."
            if warning:
                error_msg += f" {warning.rstrip('.')}."
            if feedback:
                error_msg += f" {' '.join(feedback)}"
            raise ValueError(error_msg)

        return password
