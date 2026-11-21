from models.autor import Autor
from repositories.base import BaseRepository


class AutorRepository(BaseRepository[Autor]):
    model = Autor
