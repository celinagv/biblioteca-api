from sqlmodel import col, select

from models.socio import Socio
from repositories.base import BaseRepository


class SocioRepository(BaseRepository[Socio]):
    model = Socio

    def get_by_email(self, email: str) -> Socio | None:
        """Busca al socio por email (el email es único)."""
        sentencia = select(Socio).where(col(Socio.email) == email)
        return self.session.exec(sentencia).first()
