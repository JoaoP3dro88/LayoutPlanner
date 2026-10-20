from fastapi import APIRouter

from app.domain.models import Layout, Report
from app.domain.validation import validate_layout

router = APIRouter()


@router.post("/validate", response_model=Report, summary="Valida um layout")
def validate(layout: Layout) -> Report:
    return validate_layout(layout)
