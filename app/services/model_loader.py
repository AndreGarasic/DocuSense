"""
DocuSense - Model Loader Service

Singleton class for managing ML model lifecycle (EasyOCR, QA pipeline, and LLM clients).
Models are lazily initialized and shared across the application.
"""
import logging
from abc import ABC, abstractmethod
from threading import Lock
from typing import Any

import httpx
import torch

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# =============================================================================
# LLM Client Abstraction
# =============================================================================


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM client is available."""
        pass


class OllamaClient(LLMClient):
    """Ollama LLM client for local model inference."""

    def __init__(self, base_url: str, model: str, temperature: float, max_tokens: int):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._available: bool | None = None

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate a response using Ollama API."""
        url = f"{self.base_url}/api/generate"

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        if self._available is not None:
            return self._available

        try:
            import httpx as sync_httpx

            # Check if Ollama is running
            response = sync_httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code != 200:
                self._available = False
                return False

            # Check if the model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            self._available = self.model in model_names or any(
                self.model in name for name in model_names
            )

            if not self._available:
                logger.warning(
                    f"Ollama model '{self.model}' not found. "
                    f"Available models: {model_names}. "
                    f"Run 'ollama pull {self.model}' to download it."
                )

            return self._available
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._available = False
            return False


class OpenAIClient(LLMClient):
    """OpenAI API client for cloud-based inference."""

    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: Any = None

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate a response using OpenAI API."""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content.strip()

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.api_key)


class QAPipelineWrapper:
    """
    Wrapper class that mimics the HuggingFace pipeline behavior for QA.
    
    This is needed because newer versions of transformers have changed
    the pipeline API for question-answering tasks.
    """

    def __init__(self, model: Any, tokenizer: Any):
        self.model = model
        self.tokenizer = tokenizer
        self.model.eval()

    def __call__(self, question: str, context: str) -> dict[str, Any]:
        """
        Answer a question given a context.
        
        Args:
            question: The question to answer
            context: The context containing the answer
            
        Returns:
            Dict with 'answer', 'score', 'start', 'end' keys
        """
        # Tokenize input
        inputs = self.tokenizer(
            question,
            context,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        # Get model predictions
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Get start and end logits
        start_logits = outputs.start_logits
        end_logits = outputs.end_logits

        # Get the most likely start and end positions
        start_idx = torch.argmax(start_logits, dim=1).item()
        end_idx = torch.argmax(end_logits, dim=1).item()

        # Ensure end is after start
        if end_idx < start_idx:
            end_idx = start_idx

        # Calculate confidence score (softmax of logits)
        start_probs = torch.softmax(start_logits, dim=1)
        end_probs = torch.softmax(end_logits, dim=1)
        score = (start_probs[0, start_idx] * end_probs[0, end_idx]).item()

        # Decode the answer
        input_ids = inputs["input_ids"][0]
        answer_tokens = input_ids[start_idx : end_idx + 1]
        answer = self.tokenizer.decode(answer_tokens, skip_special_tokens=True)

        return {
            "answer": answer.strip(),
            "score": score,
            "start": start_idx,
            "end": end_idx,
        }


class ModelLoader:
    """
    Singleton class for managing ML models.
    
    Provides lazy initialization and thread-safe access to:
    - EasyOCR reader for text extraction from images
    - DistilBERT QA pipeline for question answering (extractive)
    - LLM client for generative RAG (Ollama or OpenAI)
    """

    _instance: "ModelLoader | None" = None
    _lock: Lock = Lock()

    # Model instances
    _ocr_reader: Any = None
    _qa_pipeline: Any = None
    _llm_client: LLMClient | None = None

    # Initialization flags
    _ocr_initialized: bool = False
    _qa_initialized: bool = False
    _llm_initialized: bool = False
    _ocr_init_error: str | None = None
    _qa_init_error: str | None = None
    _llm_init_error: str | None = None

    def __new__(cls) -> "ModelLoader":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def ocr_reader(self) -> Any:
        """
        Get the EasyOCR reader instance.
        
        Returns None if initialization failed.
        """
        if not self._ocr_initialized:
            self._initialize_ocr()
        return self._ocr_reader

    @property
    def qa_pipeline(self) -> Any:
        """
        Get the QA pipeline instance.
        
        Returns None if initialization failed.
        """
        if not self._qa_initialized:
            self._initialize_qa()
        return self._qa_pipeline

    @property
    def ocr_available(self) -> bool:
        """Check if OCR is available."""
        return self._ocr_reader is not None

    @property
    def qa_available(self) -> bool:
        """Check if QA pipeline is available."""
        return self._qa_pipeline is not None

    @property
    def llm_client(self) -> LLMClient | None:
        """
        Get the LLM client instance.
        
        Returns None if initialization failed or provider is 'extractive'.
        """
        if not self._llm_initialized:
            self._initialize_llm()
        return self._llm_client

    @property
    def llm_available(self) -> bool:
        """Check if LLM client is available."""
        if not self._llm_initialized:
            self._initialize_llm()
        return self._llm_client is not None and self._llm_client.is_available()

    @property
    def llm_provider(self) -> str:
        """Get the configured LLM provider."""
        return settings.llm_provider

    def _initialize_ocr(self) -> None:
        """Initialize the EasyOCR reader."""
        with self._lock:
            if self._ocr_initialized:
                return

            try:
                import easyocr

                logger.info(
                    f"Loading EasyOCR reader (GPU: {settings.ocr_use_gpu}, "
                    f"languages: {settings.ocr_languages})"
                )
                self._ocr_reader = easyocr.Reader(
                    settings.ocr_languages,
                    gpu=settings.ocr_use_gpu,
                    verbose=False,
                )
                logger.info("EasyOCR reader loaded successfully")
            except Exception as e:
                self._ocr_init_error = str(e)
                logger.error(f"Failed to load EasyOCR reader: {e}")
            finally:
                self._ocr_initialized = True

    def _initialize_qa(self) -> None:
        """Initialize the QA pipeline."""
        with self._lock:
            if self._qa_initialized:
                return

            try:
                from transformers import AutoModelForQuestionAnswering, AutoTokenizer

                logger.info(f"Loading QA model: {settings.qa_model_name}")

                # Load tokenizer and model using Auto classes
                # The model name should include org: distilbert/distilbert-base-cased-distilled-squad
                tokenizer = AutoTokenizer.from_pretrained(settings.qa_model_name)
                model = AutoModelForQuestionAnswering.from_pretrained(settings.qa_model_name)

                # Create a simple wrapper that mimics pipeline behavior
                self._qa_pipeline = QAPipelineWrapper(model, tokenizer)
                logger.info("QA pipeline loaded successfully")
            except Exception as e:
                self._qa_init_error = str(e)
                logger.error(f"Failed to load QA pipeline: {e}")
            finally:
                self._qa_initialized = True

    def _initialize_llm(self) -> None:
        """Initialize the LLM client based on configured provider."""
        with self._lock:
            if self._llm_initialized:
                return

            try:
                provider = settings.llm_provider.lower()

                if provider == "extractive":
                    # Use legacy extractive QA, no LLM client needed
                    logger.info("LLM provider set to 'extractive', using DistilBERT QA")
                    self._llm_client = None

                elif provider == "ollama":
                    logger.info(
                        f"Initializing Ollama client (model: {settings.llm_model}, "
                        f"base_url: {settings.llm_base_url})"
                    )
                    self._llm_client = OllamaClient(
                        base_url=settings.llm_base_url,
                        model=settings.llm_model,
                        temperature=settings.llm_temperature,
                        max_tokens=settings.llm_max_tokens,
                    )
                    if self._llm_client.is_available():
                        logger.info("Ollama client initialized successfully")
                    else:
                        logger.warning(
                            "Ollama client initialized but model not available. "
                            "Falling back to extractive QA."
                        )

                elif provider == "openai":
                    if not settings.openai_api_key:
                        raise ValueError("OpenAI API key not configured")

                    logger.info(f"Initializing OpenAI client (model: {settings.llm_model})")
                    self._llm_client = OpenAIClient(
                        api_key=settings.openai_api_key,
                        model=settings.llm_model,
                        temperature=settings.llm_temperature,
                        max_tokens=settings.llm_max_tokens,
                    )
                    logger.info("OpenAI client initialized successfully")

                else:
                    raise ValueError(f"Unknown LLM provider: {provider}")

            except Exception as e:
                self._llm_init_error = str(e)
                logger.error(f"Failed to initialize LLM client: {e}")
            finally:
                self._llm_initialized = True

    def preload_all(self) -> dict[str, bool]:
        """
        Preload all models.
        
        Returns a dict indicating which models were loaded successfully.
        """
        logger.info("Preloading all ML models...")

        # Initialize all models
        _ = self.ocr_reader
        _ = self.qa_pipeline
        _ = self.llm_client  # Initialize LLM client

        status = {
            "ocr": self.ocr_available,
            "qa": self.qa_available,
            "llm": self.llm_available,
        }

        logger.info(f"Model preload complete: {status}")
        return status

    def cleanup(self) -> None:
        """Clean up model resources."""
        logger.info("Cleaning up ML models...")

        with self._lock:
            self._ocr_reader = None
            self._qa_pipeline = None
            self._llm_client = None
            self._ocr_initialized = False
            self._qa_initialized = False
            self._llm_initialized = False
            self._ocr_init_error = None
            self._qa_init_error = None
            self._llm_init_error = None

        logger.info("ML models cleaned up")

    def get_status(self) -> dict[str, Any]:
        """Get the status of all models."""
        return {
            "ocr": {
                "initialized": self._ocr_initialized,
                "available": self.ocr_available,
                "error": self._ocr_init_error,
            },
            "qa": {
                "initialized": self._qa_initialized,
                "available": self.qa_available,
                "error": self._qa_init_error,
            },
            "llm": {
                "initialized": self._llm_initialized,
                "available": self.llm_available,
                "provider": settings.llm_provider,
                "model": settings.llm_model,
                "error": self._llm_init_error,
            },
        }


# Global instance
_model_loader: ModelLoader | None = None


def get_model_loader() -> ModelLoader:
    """Get the global ModelLoader instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader
