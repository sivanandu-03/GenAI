from fastapi import APIRouter, HTTPException
from app.models.schemas import RecommendRequest, RecommendResponse, RoadmapStep, ResourceItem
from app.services.education_service import education_service
from app.utils.validators import validate_max_length, sanitize_text
from app.utils.logger import logger

router = APIRouter(prefix="/recommend", tags=["Personalized Learning Recommendations"])

@router.post("", response_model=RecommendResponse)
async def post_recommend(payload: RecommendRequest):
    """
    Generates a personalized study roadmap, lists resources, and practice suggestions
    based on a student's current skill level, topic, and goals.
    """
    cleaned_topic = sanitize_text(payload.topic)
    cleaned_goals = sanitize_text(payload.goals)
    
    validate_max_length(cleaned_topic, max_chars=1000, field_name="Topic")
    validate_max_length(cleaned_goals, max_chars=2000, field_name="Goals")
    
    logger.info(f"Route /recommend: topic='{cleaned_topic}' level='{payload.skill_level}'")
    
    try:
        recommendations, model_used = await education_service.get_recommendations(
            topic=cleaned_topic,
            skill_level=payload.skill_level,
            goals=cleaned_goals,
            model_pref=payload.model_preference
        )
        
        # Convert List[Dict] to objects
        roadmap_steps = [
            RoadmapStep(
                phase=step["phase"],
                title=step["title"],
                description=step["description"],
                duration=step["duration"]
            )
            for step in recommendations.get("roadmap", [])
        ]
        
        resource_items = [
            ResourceItem(
                name=res["name"],
                type=res["type"],
                description=res["description"]
            )
            for res in recommendations.get("resources", [])
        ]
        
        practice_suggestions = recommendations.get("practice_suggestions", [])
        
        return RecommendResponse(
            topic=cleaned_topic,
            skill_level=payload.skill_level,
            goals=cleaned_goals,
            roadmap=roadmap_steps,
            resources=resource_items,
            practice_suggestions=practice_suggestions,
            model_used=model_used
        )
    except Exception as err:
        logger.error(f"Route /recommend error: {err}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during recommendations compiling: {str(err)}"
        )
