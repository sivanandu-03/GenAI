import json
import re
from typing import Any, Optional
from app.utils.logger import logger

def parse_json_from_llm(text: str) -> Optional[Any]:
    """
    Attempts to extract and parse JSON structures from LLM text responses.
    Handles standard raw JSON, markdown-wrapped JSON, and partial brace segments.
    """
    if not text:
        return None

    cleaned_text = text.strip()
    
    # 1. Attempt direct parsing
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass

    # 2. Attempt parsing markdown-fenced code blocks (e.g. ```json ... ```)
    markdown_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(markdown_pattern, cleaned_text)
    if match:
        content = match.group(1).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

    # 3. Attempt extraction by finding boundaries of brackets or braces
    start_brace = cleaned_text.find('{')
    start_bracket = cleaned_text.find('[')
    
    start_idx = -1
    end_idx = -1
    
    # Decide if we're looking for an object ({}) or list ([])
    if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
        start_idx = start_brace
        end_idx = cleaned_text.rfind('}')
    elif start_bracket != -1:
        start_idx = start_bracket
        end_idx = cleaned_text.rfind(']')
        
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        raw_segment = cleaned_text[start_idx:end_idx + 1]
        try:
            return json.loads(raw_segment)
        except json.JSONDecodeError as err:
            logger.debug(f"JSON boundaries found, but failed to parse: {err}")

    logger.warning(f"Could not extract valid JSON layout from raw LLM output. Snippet: {cleaned_text[:150]}...")
    return None
