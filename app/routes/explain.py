from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ExplainRequest, ExplainResponse
from app.services.education_service import education_service
from app.utils.validators import validate_max_length, sanitize_text
from app.utils.logger import logger
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/explain", tags=["Concept Explanation"])

@router.post("", response_model=ExplainResponse)
async def post_explain(payload: ExplainRequest, current_user: dict = Depends(get_current_user)):
    """
    Requests a pedagogical explanation of a concept.
    Accommodates beginner, intermediate, and advanced comprehension levels.
    """
    cleaned_concept = sanitize_text(payload.concept)
    validate_max_length(cleaned_concept, max_chars=1000, field_name="Concept")
    
    logger.info(f"Route /explain: Explaining '{cleaned_concept}' at '{payload.level}' level.")
    
    try:
        explanation, model_used = await education_service.get_explanation(
            concept=cleaned_concept,
            level=payload.level,
            model_pref=payload.model_preference
        )
        return ExplainResponse(
            concept=cleaned_concept,
            level=payload.level,
            explanation=explanation,
            model_used=model_used
        )
    except Exception as err:
        logger.error(f"Route /explain error: {err}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during explanation rendering: {str(err)}"
        )
