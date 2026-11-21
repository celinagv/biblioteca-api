from models.autor import Autor
from repositories.autores import AutorRepository
from services.base import CrudService


class AutorService(CrudService[Autor]):
    """Los autores no tienen reglas propias: alcanza con el CRUD genérico."""

    entity_name = "Autor"

    def __init__(self, autores: AutorRepository) -> None:
        super().__init__(autores)
