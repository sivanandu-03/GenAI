from fastapi import APIRouter, HTTPException
from app.models.schemas import QuizRequest, QuizResponse, QuestionItem
from app.services.education_service import education_service
from app.utils.validators import validate_max_length, sanitize_text
from app.utils.logger import logger

router = APIRouter(prefix="/quiz", tags=["Quiz Generation"])

@router.post("", response_model=QuizResponse)
async def post_quiz(payload: QuizRequest):
    """
    Generates a structured, multiple-choice quiz about a specific topic.
    Difficulty options: Easy, Medium, Hard. Question range: 1 to 10.
    """
    cleaned_topic = sanitize_text(payload.topic)
    validate_max_length(cleaned_topic, max_chars=1000, field_name="Topic")
    
    logger.info(f"Route /quiz: Request topic='{cleaned_topic}' diff='{payload.difficulty}' count={payload.num_questions}")
    
    try:
        questions, model_used = await education_service.generate_quiz(
            topic=cleaned_topic,
            difficulty=payload.difficulty,
            num_questions=payload.num_questions,
            model_pref=payload.model_preference
        )
        
        # Convert List[Dict] to List[QuestionItem]
        question_items = []
        for q in questions:
            question_items.append(
                QuestionItem(
                    questionText=q["questionText"],
                    options=q["options"],
                    correctAnswer=q["correctAnswer"],
                    explanation=q["explanation"]
                )
            )
            
        return QuizResponse(
            topic=cleaned_topic,
            difficulty=payload.difficulty,
            questions=question_items,
            model_used=model_used
        )
    except Exception as err:
        logger.error(f"Route /quiz error: {err}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during quiz generation: {str(err)}"
        )
