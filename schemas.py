
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    course: str = Field(min_length=1, max_length=200)


class GenerationRequest(BaseModel):
    recipients: list[RecipientInput] = Field(
        min_length=1,
        max_length=500,
    )


class RecipientResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    status: str
    error: str | None = None
