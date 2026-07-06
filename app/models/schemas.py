from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

# --- Q&A Models ---
class QARequest(BaseModel):
    question: str = Field(..., min_length=5, description="The educational question to ask.")
    model_preference: Optional[str] = Field(None, description="Preferred model provider ('gemini' or 'lamini').")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question cannot be empty or only whitespace.")
        return v

class QAResponse(BaseModel):
    question: str
    answer: str
    model_used: str

# --- Concept Explanation Models ---
class ExplainRequest(BaseModel):
    concept: str = Field(..., min_length=2, description="The concept to explain.")
    level: str = Field("Intermediate", description="Explanation level ('Beginner', 'Intermediate', 'Advanced').")
    model_preference: Optional[str] = Field(None, description="Preferred model provider.")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = ["Beginner", "Intermediate", "Advanced"]
        v_title = v.strip().title()
        if v_title not in allowed:
            raise ValueError(f"Level must be one of {allowed}")
        return v_title

class ExplainResponse(BaseModel):
    concept: str
    level: str
    explanation: str
    model_used: str

# --- Quiz Generation Models ---
class QuestionItem(BaseModel):
    question_text: str = Field(..., alias="questionText")
    options: List[str] = Field(..., min_items=2, max_items=6, description="Multiple choice options.")
    correct_answer: str = Field(..., alias="correctAnswer", description="The exact text or label matching the correct option.")
    explanation: str = Field(..., description="Explanation of why this answer is correct.")

    class Config:
        populate_by_name = True

class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="The topic of the quiz.")
    difficulty: str = Field("Medium", description="Quiz difficulty level ('Easy', 'Medium', 'Hard').")
    num_questions: int = Field(5, ge=1, le=10, description="Number of questions to generate (1 to 10).")
    model_preference: Optional[str] = Field(None, description="Preferred model provider.")

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        allowed = ["Easy", "Medium", "Hard"]
        v_title = v.strip().title()
        if v_title not in allowed:
            raise ValueError(f"Difficulty must be one of {allowed}")
        return v_title

class QuizResponse(BaseModel):
    topic: str
    difficulty: str
    questions: List[QuestionItem]
    model_used: str

# --- Educational Summarization Models ---
class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10, description="The text or notes to summarize.")
    format: str = Field("Concise", description="Summary style ('Concise', 'Detailed', 'Bullet-point').")
    model_preference: Optional[str] = Field(None, description="Preferred model provider.")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        allowed = ["Concise", "Detailed", "Bullet-point"]
        # Allow variations like 'bullet-point', 'bulletpoint', 'Bullet-point'
        v_normalized = v.strip().title()
        if v_normalized == "Bullet-Points" or v_normalized == "Bulletpoint" or v_normalized == "Bullet Points":
            v_normalized = "Bullet-point"
        if v_normalized not in allowed:
            raise ValueError(f"Format must be one of {allowed}")
        return v_normalized

class SummarizeResponse(BaseModel):
    original_length: int
    summary_length: int
    summary: str
    format: str
    model_used: str

# --- Personalized Recommendation Models ---
class ResourceItem(BaseModel):
    name: str = Field(..., description="Name of the resource.")
    type: str = Field(..., description="Type of resource (e.g. Book, Video, Course, Article).")
    description: str = Field(..., description="Brief description of the resource.")

class RoadmapStep(BaseModel):
    phase: str = Field(..., description="Phase index or title (e.g. Phase 1, Week 1).")
    title: str = Field(..., description="Title of what to learn.")
    description: str = Field(..., description="Details on what to learn.")
    duration: str = Field(..., description="Estimated study duration.")

class RecommendRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="The topic to learn.")
    skill_level: str = Field("Beginner", description="Current skill level ('Beginner', 'Intermediate', 'Advanced').")
    goals: str = Field(..., min_length=5, description="Learning goals or objectives.")
    model_preference: Optional[str] = Field(None, description="Preferred model provider.")

    @field_validator("skill_level")
    @classmethod
    def validate_skill_level(cls, v: str) -> str:
        allowed = ["Beginner", "Intermediate", "Advanced"]
        v_title = v.strip().title()
        if v_title not in allowed:
            raise ValueError(f"Skill level must be one of {allowed}")
        return v_title

class RecommendResponse(BaseModel):
    topic: str
    skill_level: str
    goals: str
    roadmap: List[RoadmapStep]
    resources: List[ResourceItem]
    practice_suggestions: List[str]
    model_used: str

# --- Authentication Models ---
class UserSignupRequest(BaseModel):
    email: str = Field(..., description="User's email address.")
    username: str = Field(..., min_length=3, max_length=50, description="User's unique username.")
    password: str = Field(..., min_length=6, description="User's password (min 6 characters).")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v:
            raise ValueError("Invalid email format.")
        return v

class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User's email address.")
    password: str = Field(..., description="User's password.")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()

class UserResponse(BaseModel):
    email: str
    username: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

