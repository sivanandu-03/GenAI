from fastapi import HTTPException
from app.utils.logger import logger

def validate_max_length(text: str, max_chars: int = 8000, field_name: str = "Input text") -> str:
    """Validates that input text does not exceed the allowed maximum character limit."""
    char_count = len(text)
    if char_count > max_chars:
        logger.warning(f"Validation failed: {field_name} length ({char_count}) exceeds limit of {max_chars} chars.")
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} is too long. Maximum allowed characters is {max_chars} (received {char_count})."
        )
    return text

def sanitize_text(text: str) -> str:
    """Cleans input text by stripping leading/trailing whitespace."""
    if not text:
        return ""
    # We strip whitespaces
    return text.strip()
