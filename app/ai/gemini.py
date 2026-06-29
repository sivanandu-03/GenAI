import asyncio
import google.generativeai as genai
from app.config import settings
from app.utils.logger import logger

class GeminiClient:
    """Client wrapper for Google Gemini Generative AI Services."""
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.is_configured = settings.is_gemini_configured()
        
        if self.is_configured:
            # Configure the Google GenAI SDK
            genai.configure(api_key=self.api_key)
            self.model_name = settings.GEMINI_MODEL_NAME
            logger.info(f"GeminiClient initialized successfully with model '{self.model_name}'.")
        else:
            logger.warning("GeminiClient: GEMINI_API_KEY is missing. Gemini requests will fail.")

    async def generate(self, prompt: str) -> str:
        """
        Generates content for a given prompt string.
        Executes in an executor thread to remain non-blocking.
        """
        if not self.is_configured:
            raise ValueError(
                "Gemini API key is not configured. Please add a valid GEMINI_API_KEY in your .env file."
            )

        try:
            model = genai.GenerativeModel(self.model_name)
            loop = asyncio.get_event_loop()
            
            # Execute SDK request inside the default threadpool executor
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(prompt)
            )
            
            if not response.text:
                raise ValueError("Received empty response from Gemini model.")
                
            return response.text

        except Exception as err:
            logger.error(f"Gemini API generation error (using {self.model_name}): {err}")
            
            # Fallback strategy: Try gemini-2.0-flash
            if self.model_name != "gemini-2.0-flash":
                try:
                    logger.info("Attempting fallback to gemini-2.0-flash...")
                    fallback_model = genai.GenerativeModel("gemini-2.0-flash")
                    
                    response = await loop.run_in_executor(
                        None,
                        lambda: fallback_model.generate_content(prompt)
                    )
                    return response.text
                except Exception as fallback_err:
                    logger.critical(f"Gemini Fallback client failed: {fallback_err}")
                    raise fallback_err
            raise err

# Export instantiated client singleton
gemini_client = GeminiClient()
