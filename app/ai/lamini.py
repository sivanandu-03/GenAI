import asyncio
from app.config import settings
from app.utils.logger import logger

class LaMiniClient:
    """Client wrapper for local LaMini-Flan-T5 HuggingFace model inference using direct model classes."""
    def __init__(self):
        self.model_name = settings.LAMINI_MODEL_NAME
        self.model = None
        self.tokenizer = None
        self.device_name = "cpu"
        self._lock = asyncio.Lock()

    def _load_model(self):
        """Loads model and tokenizer weights. Executed in a threadpool."""
        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            
            logger.info(
                f"LaMiniClient: Loading model '{self.model_name}' directly using AutoModel classes. "
                "This will fetch weights (~990MB) on the first run if not already cached."
            )
            
            # Create local cache folder
            settings.HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            
            # Select CPU/GPU device
            self.device_name = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"LaMiniClient: Selected inference device: {self.device_name} (cuda.is_available={torch.cuda.is_available()})")

            # Load tokenizer and seq2seq model
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(settings.HF_CACHE_DIR)
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                cache_dir=str(settings.HF_CACHE_DIR)
            )
            
            # Transfer model parameters to GPU if active
            self.model.to(self.device_name)
            logger.info("LaMiniClient: Model and tokenizer loaded successfully.")
            
        except ImportError as err:
            logger.error("LaMiniClient: required libraries 'torch' or 'transformers' are not available.")
            raise RuntimeError("Local model dependencies are not satisfied.") from err
        except Exception as err:
            logger.critical(f"LaMiniClient: Failed to load model weights: {err}")
            raise err

    async def generate(self, prompt: str) -> str:
        """
        Generates text using the local LaMini model.
        Initializes the model on-demand if it hasn't been loaded.
        """
        # Ensure thread-safe lazy-loading of model weights
        async with self._lock:
            if self.model is None or self.tokenizer is None:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._load_model)

        if self.model is None or self.tokenizer is None:
            raise RuntimeError("LaMini model could not be initialized.")

        try:
            # Context length safety truncation for T5 models (max input length is generally 512 tokens)
            truncated_prompt = prompt
            if len(prompt.split()) > 450:
                logger.warning("LaMiniClient: Prompt length is high for T5. Truncating to prevent overflow.")
                truncated_prompt = " ".join(prompt.split()[:450])

            loop = asyncio.get_event_loop()
            
            def run_inference():
                import torch
                
                # Tokenize input text
                inputs = self.tokenizer(truncated_prompt, return_tensors="pt")
                # Move tensors to the selected device (CPU/GPU)
                inputs = {k: v.to(self.device_name) for k, v in inputs.items()}
                
                # Run generation
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_length=512,
                        temperature=0.7,
                        do_sample=True,
                        num_return_sequences=1
                    )
                
                # Decode and return string
                response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                return response_text

            output = await loop.run_in_executor(None, run_inference)
            return output
            
        except Exception as err:
            logger.error(f"LaMiniClient: Inference error: {err}")
            raise err

# Export instantiated client singleton
lamini_client = LaMiniClient()
