from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import QARequest, QAResponse
from app.services.education_service import education_service
from app.utils.validators import validate_max_length, sanitize_text
from app.utils.logger import logger
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/qa", tags=["Educational QA"])

@router.post("", response_model=QAResponse)
async def post_qa(payload: QARequest, current_user: dict = Depends(get_current_user)):
    """
    Submits an educational question and returns a detailed answer.
    Routes to Gemini or LaMini as preferred.
    """
    cleaned_question = sanitize_text(payload.question)
    validate_max_length(cleaned_question, max_chars=4000, field_name="Question")

    logger.info(f"Route /qa: Received question. Length: {len(cleaned_question)}")
    
    try:
        answer, model_used = await education_service.get_qa_answer(
            question=cleaned_question,
            model_pref=payload.model_preference
        )
        return QAResponse(
            question=cleaned_question,
            answer=answer,
            model_used=model_used
        )
    except Exception as err:
        logger.error(f"Route /qa error: {err}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during Q&A processing: {str(err)}"
        )
