from fastapi import APIRouter

from api.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")
