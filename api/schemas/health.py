from sqlmodel import SQLModel


class HealthResponse(SQLModel):
    status: str
