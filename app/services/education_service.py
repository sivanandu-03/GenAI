from typing import Tuple, List, Dict, Any, Optional
from app.config import settings
from app.utils.logger import logger
from app.utils.formatter import parse_json_from_llm
from app.ai.gemini import gemini_client
from app.ai.lamini import lamini_client

# Import Prompts
from app.prompts.qa import QA_PROMPT_TEMPLATE
from app.prompts.explain import EXPLAIN_PROMPT_TEMPLATE
from app.prompts.quiz import QUIZ_PROMPT_TEMPLATE
from app.prompts.summary import SUMMARY_PROMPT_TEMPLATE
from app.prompts.recommend import RECOMMEND_PROMPT_TEMPLATE

class EducationService:
    """Orchestrates prompts construction, model execution, formatting, and fallback management."""

    async def _execute_generation(self, prompt: str, preferred_provider: Optional[str]) -> Tuple[str, str]:
        """
        Executes text generation using the preferred provider, with automatic fallback
        if the primary choice throws an error.
        Returns:
            Tuple[response_text, provider_used]
        """
        # Determine initial provider based on user preference or settings default
        provider = preferred_provider.lower() if preferred_provider else settings.DEFAULT_MODEL
        if provider not in ("gemini", "lamini"):
            provider = "gemini"
            
        logger.info(f"EducationService: Route requested provider='{provider}'")

        # Case 1: Primary provider is local LaMini
        if provider == "lamini":
            try:
                response = await lamini_client.generate(prompt)
                return response, "LaMini-Flan-T5"
            except Exception as err:
                logger.error(f"EducationService: LaMini inference failed ({err}). Attempting fallback to Gemini...")
                if settings.is_gemini_configured():
                    try:
                        response = await gemini_client.generate(prompt)
                        return response, "Gemini 1.5 Pro (LaMini Fallback)"
                    except Exception as gemini_err:
                        logger.critical(f"EducationService: Gemini fallback also failed ({gemini_err}).")
                        raise RuntimeError("Both LaMini and Gemini models failed to generate content.") from gemini_err
                else:
                    logger.error("EducationService: Gemini is not configured. Cannot perform fallback.")
                    raise RuntimeError("LaMini failed and Gemini is not configured in settings.") from err

        # Case 2: Primary provider is Google Gemini
        else:
            try:
                response = await gemini_client.generate(prompt)
                return response, "Gemini 1.5 Pro"
            except Exception as err:
                logger.error(f"EducationService: Gemini generation failed ({err}). Attempting fallback to LaMini...")
                try:
                    response = await lamini_client.generate(prompt)
                    return response, "LaMini-Flan-T5 (Gemini Fallback)"
                except Exception as lamini_err:
                    logger.critical(f"EducationService: LaMini fallback also failed ({lamini_err}).")
                    raise RuntimeError("Both Gemini and LaMini models failed to generate content.") from lamini_err

    async def get_qa_answer(self, question: str, model_pref: Optional[str] = None) -> Tuple[str, str]:
        """Runs Question Answering."""
        prompt = QA_PROMPT_TEMPLATE.format(question=question)
        return await self._execute_generation(prompt, model_pref)

    async def get_explanation(self, concept: str, level: str, model_pref: Optional[str] = None) -> Tuple[str, str]:
        """Runs concept explanation."""
        prompt = EXPLAIN_PROMPT_TEMPLATE.format(concept=concept, level=level)
        return await self._execute_generation(prompt, model_pref)

    async def get_summary(self, text: str, format_style: str, model_pref: Optional[str] = None) -> Tuple[str, str]:
        """Runs text summarization."""
        prompt = SUMMARY_PROMPT_TEMPLATE.format(text=text, format=format_style)
        return await self._execute_generation(prompt, model_pref)

    async def generate_quiz(
        self, topic: str, difficulty: str, num_questions: int, model_pref: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Runs Quiz generation, verifying JSON format.
        Falls back to Gemini if the first option returns unparsable JSON.
        Returns a hardcoded mock if both models fail.
        """
        prompt = QUIZ_PROMPT_TEMPLATE.format(topic=topic, difficulty=difficulty, num_questions=num_questions)
        provider = model_pref.lower() if model_pref else settings.DEFAULT_MODEL
        
        try:
            raw_text, used_provider = await self._execute_generation(prompt, provider)
            parsed_json = parse_json_from_llm(raw_text)
            
            if parsed_json and isinstance(parsed_json, list) and len(parsed_json) > 0:
                # Structure validation
                validated_questions = []
                for item in parsed_json:
                    if (
                        isinstance(item, dict)
                        and any(k in item for k in ("questionText", "question_text"))
                        and "options" in item
                        and any(k in item for k in ("correctAnswer", "correct_answer"))
                    ):
                        # Standardize keys to camelCase for frontend consistency
                        q_text = item.get("questionText", item.get("question_text", ""))
                        options = item.get("options", [])
                        c_ans = item.get("correctAnswer", item.get("correct_answer", ""))
                        explanation = item.get("explanation", "No explanation provided.")
                        
                        validated_questions.append({
                            "questionText": q_text,
                            "options": options,
                            "correctAnswer": c_ans,
                            "explanation": explanation
                        })
                
                if validated_questions:
                    return validated_questions, used_provider
            
            raise ValueError("LaMini or Gemini response was not formatted as a valid MCQ array.")

        except Exception as err:
            logger.warning(f"EducationService.generate_quiz: provider '{provider}' failed JSON validation ({err}).")
            
            # Format Fallback: if we haven't tried Gemini yet, try Gemini explicitly
            if provider != "gemini" and settings.is_gemini_configured():
                logger.info("EducationService: Format fallback triggered. Retrying Quiz with Gemini...")
                try:
                    raw_text, used_provider = await self._execute_generation(prompt, "gemini")
                    parsed_json = parse_json_from_llm(raw_text)
                    if parsed_json and isinstance(parsed_json, list):
                        validated_questions = []
                        for item in parsed_json:
                            q_text = item.get("questionText", item.get("question_text", ""))
                            options = item.get("options", [])
                            c_ans = item.get("correctAnswer", item.get("correct_answer", ""))
                            explanation = item.get("explanation", "No explanation provided.")
                            if q_text and options and c_ans:
                                validated_questions.append({
                                    "questionText": q_text,
                                    "options": options,
                                    "correctAnswer": c_ans,
                                    "explanation": explanation
                                })
                        if validated_questions:
                            return validated_questions, f"{used_provider} (format fallback)"
                except Exception as fallback_err:
                    logger.error(f"EducationService: Format fallback also failed: {fallback_err}")
            
            # Robust return of a mock quiz to keep the client operational
            logger.error("EducationService: Returning mock quiz template.")
            mock_quiz = [
                {
                    "questionText": f"Which of the following describes the core theme of {topic}?",
                    "options": [
                        f"Fundamental theory of {topic}",
                        f"Applied mechanics of {topic}",
                        f"History and evolution of {topic}",
                        "None of the above"
                    ],
                    "correctAnswer": f"Fundamental theory of {topic}",
                    "explanation": f"This is an educational mock question because the AI service failed to compile a custom quiz for topic: {topic}."
                }
            ]
            return mock_quiz, "Mock Generator (Fallback)"

    async def get_recommendations(
        self, topic: str, skill_level: str, goals: str, model_pref: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Runs recommendation engine.
        Falls back to Gemini if the first option returns unparsable JSON.
        Returns a hardcoded mock if both models fail.
        """
        prompt = RECOMMEND_PROMPT_TEMPLATE.format(topic=topic, skill_level=skill_level, goals=goals)
        provider = model_pref.lower() if model_pref else settings.DEFAULT_MODEL
        
        try:
            raw_text, used_provider = await self._execute_generation(prompt, provider)
            parsed_json = parse_json_from_llm(raw_text)
            
            if (
                parsed_json
                and isinstance(parsed_json, dict)
                and "roadmap" in parsed_json
                and "resources" in parsed_json
                and "practice_suggestions" in parsed_json
            ):
                return parsed_json, used_provider
                
            raise ValueError("Model response did not contain the required recommendation fields.")

        except Exception as err:
            logger.warning(f"EducationService.get_recommendations: provider '{provider}' failed JSON validation ({err}).")
            
            if provider != "gemini" and settings.is_gemini_configured():
                logger.info("EducationService: Format fallback triggered. Retrying Recommendations with Gemini...")
                try:
                    raw_text, used_provider = await self._execute_generation(prompt, "gemini")
                    parsed_json = parse_json_from_llm(raw_text)
                    if (
                        parsed_json
                        and isinstance(parsed_json, dict)
                        and "roadmap" in parsed_json
                        and "resources" in parsed_json
                    ):
                        # Parse suggestions safely
                        practice_s = parsed_json.get("practice_suggestions", parsed_json.get("practiceSuggestions", []))
                        parsed_json["practice_suggestions"] = practice_s
                        return parsed_json, f"{used_provider} (format fallback)"
                except Exception as fallback_err:
                    logger.error(f"EducationService: Format fallback also failed: {fallback_err}")
            
            # Robust mock return
            logger.error("EducationService: Returning mock recommendations template.")
            mock_recs = {
                "roadmap": [
                    {
                        "phase": "Phase 1: Getting Started",
                        "title": f"Introduction to {topic}",
                        "description": f"Learn the syntax, definitions, and foundation of {topic}.",
                        "duration": "1 week"
                    },
                    {
                        "phase": "Phase 2: Deep Dive",
                        "title": "Intermediate Operations",
                        "description": "Understand parameters, references, and core features.",
                        "duration": "2 weeks"
                    }
                ],
                "resources": [
                    {
                        "name": f"Official {topic} documentation",
                        "type": "Article",
                        "description": "Primary documentation recommended for beginners."
                    },
                    {
                        "name": f"Comprehensive Guide to {topic}",
                        "type": "Course",
                        "description": "Free tutorial series covering beginner to intermediate concepts."
                    }
                ],
                "practice_suggestions": [
                    f"Set up your development environment and print a hello-world style output for {topic}.",
                    f"Solve 3 beginner problems related to {topic} online."
                ]
            }
            return mock_recs, "Mock Generator (Fallback)"

# Export coordination service singleton
education_service = EducationService()
