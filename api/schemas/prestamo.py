from datetime import date

from pydantic import BaseModel, ConfigDict

from api.schemas.base import ReadSchema
from api.schemas.types import IdField


class PrestamoCreate(BaseModel):
    socio_id: IdField
    libro_id: IdField

    model_config = ConfigDict(json_schema_extra={"examples": [{"socio_id": 2, "libro_id": 3}]})


class PrestamoRead(ReadSchema):
    id: int
    socio_id: int
    libro_id: int
    fecha_prestamo: date
    fecha_vencimiento: date
    fecha_devolucion: date | None
    multa: int
