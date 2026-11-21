from sqlmodel import Field, SQLModel


class LibroAutor(SQLModel, table=True):
    """Tabla puente que resuelve la relación muchos-a-muchos entre libros y autores."""

    __tablename__ = "libro_autor"  # pyright: ignore[reportAssignmentType]

    libro_id: int = Field(foreign_key="libro.id", primary_key=True, ondelete="CASCADE")
    autor_id: int = Field(foreign_key="autor.id", primary_key=True, ondelete="CASCADE")
