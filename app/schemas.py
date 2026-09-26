from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["admin", "encargado"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=4, max_length=128)
    role: Role


class UserResponse(BaseModel):
    username: str
    email: EmailStr
    role: Role
    display_name: str


class LoginResponse(BaseModel):
    message: str
    user: UserResponse


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=4, max_length=128)
    email: EmailStr
    role: Role
    display_name: str = Field(min_length=3, max_length=120)

    @field_validator("username", "display_name")
    @classmethod
    def strip_user_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El campo no puede estar vacio")
        return cleaned


class UserUpdate(BaseModel):
    password: str | None = Field(default=None, min_length=4, max_length=128)
    email: EmailStr | None = None
    role: Role | None = None
    display_name: str | None = Field(default=None, min_length=3, max_length=120)


class UserListResponse(UserResponse):
    id: str


class EvaluationCreate(BaseModel):
    title: str = Field(min_length=5, max_length=160)
    description: str = Field(min_length=10, max_length=2000)
    area: str = Field(min_length=2, max_length=120)
    assigned_to: str = Field(min_length=3, max_length=80)
    due_date: datetime

    @field_validator("title", "description", "area", "assigned_to")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El campo no puede estar vacio")
        return cleaned


class EvaluationProgressUpdate(BaseModel):
    progress: int = Field(ge=0, le=100)
    evidence: str = Field(min_length=5, max_length=4000)

    @field_validator("evidence")
    @classmethod
    def clean_evidence(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("La evidencia no puede estar vacia")
        return cleaned


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    description: str
    area: str
    assigned_to: str
    due_date: datetime
    progress: int
    evidence: str
    status: str
    created_at: datetime
    updated_at: datetime


class AnalysisResponse(BaseModel):
    evaluation_id: str
    score: int = Field(ge=0, le=100)
    summary: str
    processed_in_seconds: float
