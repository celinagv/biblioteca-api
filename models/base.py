from sqlmodel import Field, SQLModel


class IdModel(SQLModel):
    """Base común de las tablas: aporta una clave primaria autoincremental."""

    id: int | None = Field(default=None, primary_key=True)
