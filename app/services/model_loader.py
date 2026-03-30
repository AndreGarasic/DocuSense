"""
DocuSense - Model Loader Service

Singleton class for managing ML model lifecycle (EasyOCR and QA pipeline).
Models are lazily initialized and shared across the application.
"""
import logging
from threading import Lock
from typing import Any

import torch

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


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
    - DistilBERT QA pipeline for question answering
    """

    _instance: "ModelLoader | None" = None
    _lock: Lock = Lock()

    # Model instances
    _ocr_reader: Any = None
    _qa_pipeline: Any = None

    # Initialization flags
    _ocr_initialized: bool = False
    _qa_initialized: bool = False
    _ocr_init_error: str | None = None
    _qa_init_error: str | None = None

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

    def preload_all(self) -> dict[str, bool]:
        """
        Preload all models.
        
        Returns a dict indicating which models were loaded successfully.
        """
        logger.info("Preloading all ML models...")
        
        # Initialize both models
        _ = self.ocr_reader
        _ = self.qa_pipeline

        status = {
            "ocr": self.ocr_available,
            "qa": self.qa_available,
        }
        
        logger.info(f"Model preload complete: {status}")
        return status

    def cleanup(self) -> None:
        """Clean up model resources."""
        logger.info("Cleaning up ML models...")
        
        with self._lock:
            self._ocr_reader = None
            self._qa_pipeline = None
            self._ocr_initialized = False
            self._qa_initialized = False
            self._ocr_init_error = None
            self._qa_init_error = None

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
        }


# Global instance
_model_loader: ModelLoader | None = None


def get_model_loader() -> ModelLoader:
    """Get the global ModelLoader instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader
