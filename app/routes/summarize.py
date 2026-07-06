from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import SummarizeRequest, SummarizeResponse
from app.services.education_service import education_service
from app.utils.validators import validate_max_length, sanitize_text
from app.utils.logger import logger
from app.utils.auth_helper import get_current_user

router = APIRouter(prefix="/summarize", tags=["Educational Summarization"])

@router.post("", response_model=SummarizeResponse)
async def post_summarize(payload: SummarizeRequest, current_user: dict = Depends(get_current_user)):
    """
    Summarizes notes, chapters, or paragraphs into Concise, Detailed, or Bullet-point formats.
    """
    cleaned_text = sanitize_text(payload.text)
    # Allow up to 12,000 characters for long paragraphs or notes
    validate_max_length(cleaned_text, max_chars=12000, field_name="Text to summarize")
    
    logger.info(f"Route /summarize: Request length={len(cleaned_text)} format='{payload.format}'")
    
    try:
        summary, model_used = await education_service.get_summary(
            text=cleaned_text,
            format_style=payload.format,
            model_pref=payload.model_preference
        )
        return SummarizeResponse(
            original_length=len(cleaned_text),
            summary_length=len(summary),
            summary=summary,
            format=payload.format,
            model_used=model_used
        )
    except Exception as err:
        logger.error(f"Route /summarize error: {err}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during summarization: {str(err)}"
        )
