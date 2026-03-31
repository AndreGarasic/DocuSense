"""
DocuSense - QA Service Tests

Unit tests for the QAService.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.qa import AnswerResponse, ChunkReference
from app.services.qa_service import QAService


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def mock_model_loader():
    """Create a mock model loader with QA pipeline (extractive mode)."""
    with patch("app.services.qa_service.get_model_loader") as mock_loader:
        mock_instance = MagicMock()
        mock_instance.qa_available = True
        mock_instance.llm_available = False  # Use extractive QA by default
        mock_instance.llm_client = None
        mock_instance.llm_provider = "extractive"
        mock_instance.qa_pipeline = MagicMock()
        mock_instance.qa_pipeline.return_value = {
            "answer": "Test answer",
            "score": 0.85,
        }
        mock_loader.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def qa_service(mock_db, mock_model_loader):
    """Create a QAService instance with mocked dependencies."""
    # Clear cache before each test
    QAService.clear_cache()
    
    service = QAService(mock_db)
    return service


class TestQAServiceCache:
    """Tests for QA caching functionality."""

    def test_cache_key_generation(self, qa_service):
        """Test that cache keys are generated consistently."""
        key1 = qa_service._generate_cache_key(
            "What is the total?", "session-123", None
        )
        key2 = qa_service._generate_cache_key(
            "What is the total?", "session-123", None
        )
        
        assert key1 == key2

    def test_cache_key_different_questions(self, qa_service):
        """Test that different questions produce different cache keys."""
        key1 = qa_service._generate_cache_key(
            "What is the total?", "session-123", None
        )
        key2 = qa_service._generate_cache_key(
            "Who is the CEO?", "session-123", None
        )
        
        assert key1 != key2

    def test_cache_key_different_sessions(self, qa_service):
        """Test that different sessions produce different cache keys."""
        key1 = qa_service._generate_cache_key(
            "What is the total?", "session-123", None
        )
        key2 = qa_service._generate_cache_key(
            "What is the total?", "session-456", None
        )
        
        assert key1 != key2

    def test_cache_key_different_document_ids(self, qa_service):
        """Test that different document IDs produce different cache keys."""
        key1 = qa_service._generate_cache_key(
            "What is the total?", "session-123", [1, 2]
        )
        key2 = qa_service._generate_cache_key(
            "What is the total?", "session-123", [1, 2, 3]
        )
        
        assert key1 != key2

    def test_cache_key_normalized_question(self, qa_service):
        """Test that questions are normalized (case-insensitive, trimmed)."""
        key1 = qa_service._generate_cache_key(
            "What is the total?", "session-123", None
        )
        key2 = qa_service._generate_cache_key(
            "  WHAT IS THE TOTAL?  ", "session-123", None
        )
        
        assert key1 == key2

    def test_cache_key_document_ids_order_independent(self, qa_service):
        """Test that document ID order doesn't affect cache key."""
        key1 = qa_service._generate_cache_key(
            "What is the total?", "session-123", [1, 2, 3]
        )
        key2 = qa_service._generate_cache_key(
            "What is the total?", "session-123", [3, 1, 2]
        )
        
        assert key1 == key2

    def test_clear_cache(self, qa_service):
        """Test cache clearing."""
        # Add something to cache
        QAService._cache["test_key"] = "test_value"
        
        count = QAService.clear_cache()
        
        assert count >= 1
        assert QAService.get_cache_size() == 0

    def test_get_cache_size(self, qa_service):
        """Test getting cache size."""
        QAService.clear_cache()
        
        assert QAService.get_cache_size() == 0
        
        QAService._cache["key1"] = "value1"
        QAService._cache["key2"] = "value2"
        
        assert QAService.get_cache_size() == 2


class TestQAServiceAnswerQuestion:
    """Tests for the answer_question method."""

    @pytest.mark.asyncio
    async def test_answer_question_qa_unavailable(self, mock_db):
        """Test answer_question when both LLM and QA model are unavailable."""
        with patch("app.services.qa_service.get_model_loader") as mock_loader:
            mock_instance = MagicMock()
            mock_instance.qa_available = False
            mock_instance.llm_available = False  # Both unavailable
            mock_loader.return_value = mock_instance
            
            service = QAService(mock_db)
            
            response = await service.answer_question(
                "What is the total?", "session-123"
            )
            
            assert "unavailable" in response.answer.lower()
            assert response.confidence == 0.0
            assert response.cached is False

    @pytest.mark.asyncio
    async def test_answer_question_no_chunks(self, qa_service, mock_db):
        """Test answer_question when no relevant chunks are found."""
        # Mock the chunk retrieval to return empty list
        with patch.object(
            qa_service, "_retrieve_relevant_chunks", new_callable=AsyncMock
        ) as mock_retrieve:
            mock_retrieve.return_value = []
            
            response = await qa_service.answer_question(
                "What is the total?", "session-123"
            )
            
            assert "no relevant documents" in response.answer.lower()
            assert response.confidence == 0.0
            assert len(response.source_chunks) == 0

    @pytest.mark.asyncio
    async def test_answer_question_with_chunks(self, qa_service, mock_db):
        """Test answer_question with relevant chunks."""
        # Create mock chunks
        mock_chunk = MagicMock()
        mock_chunk.content = "The total amount is $100.00"
        mock_chunk.chunk_index = 0
        
        mock_document = MagicMock()
        mock_document.id = 1
        mock_document.original_filename = "invoice.pdf"
        
        # Mock the chunk retrieval
        with patch.object(
            qa_service, "_retrieve_relevant_chunks", new_callable=AsyncMock
        ) as mock_retrieve:
            mock_retrieve.return_value = [(mock_chunk, mock_document, 0.95)]
            
            response = await qa_service.answer_question(
                "What is the total?", "session-123"
            )
            
            assert response.answer == "Test answer"
            assert response.confidence == 0.85
            assert len(response.source_chunks) == 1
            assert response.source_chunks[0].document_id == 1

    @pytest.mark.asyncio
    async def test_answer_question_cached_response(self, qa_service, mock_db):
        """Test that repeated questions return cached responses."""
        # Create mock chunks
        mock_chunk = MagicMock()
        mock_chunk.content = "The total amount is $100.00"
        mock_chunk.chunk_index = 0
        
        mock_document = MagicMock()
        mock_document.id = 1
        mock_document.original_filename = "invoice.pdf"
        
        with patch.object(
            qa_service, "_retrieve_relevant_chunks", new_callable=AsyncMock
        ) as mock_retrieve:
            mock_retrieve.return_value = [(mock_chunk, mock_document, 0.95)]
            
            # First call
            response1 = await qa_service.answer_question(
                "What is the total?", "session-123"
            )
            assert response1.cached is False
            
            # Second call (should be cached)
            response2 = await qa_service.answer_question(
                "What is the total?", "session-123"
            )
            assert response2.cached is True
            
            # Retrieve should only be called once
            assert mock_retrieve.call_count == 1


class TestQAServiceBuildContext:
    """Tests for context building."""

    def test_build_context_single_chunk(self, qa_service):
        """Test building context from a single chunk."""
        mock_chunk = MagicMock()
        mock_chunk.content = "This is the chunk content."
        mock_chunk.chunk_index = 0
        
        mock_document = MagicMock()
        mock_document.id = 1
        mock_document.original_filename = "test.pdf"
        
        chunks = [(mock_chunk, mock_document, 0.9)]
        
        context, references = qa_service._build_context(chunks)
        
        assert "This is the chunk content." in context
        assert len(references) == 1
        assert references[0].document_id == 1
        assert references[0].similarity_score == 0.9

    def test_build_context_multiple_chunks(self, qa_service):
        """Test building context from multiple chunks."""
        chunks = []
        for i in range(3):
            mock_chunk = MagicMock()
            mock_chunk.content = f"Chunk {i} content."
            mock_chunk.chunk_index = i
            
            mock_document = MagicMock()
            mock_document.id = i + 1
            mock_document.original_filename = f"doc{i}.pdf"
            
            chunks.append((mock_chunk, mock_document, 0.9 - i * 0.1))
        
        context, references = qa_service._build_context(chunks)
        
        assert "Chunk 0 content." in context
        assert "Chunk 1 content." in context
        assert "Chunk 2 content." in context
        assert len(references) == 3

    def test_build_context_truncates_long_preview(self, qa_service):
        """Test that long chunk content is truncated in preview."""
        mock_chunk = MagicMock()
        mock_chunk.content = "A" * 500  # Long content
        mock_chunk.chunk_index = 0
        
        mock_document = MagicMock()
        mock_document.id = 1
        mock_document.original_filename = "test.pdf"
        
        chunks = [(mock_chunk, mock_document, 0.9)]
        
        _, references = qa_service._build_context(chunks)
        
        # Preview should be truncated to ~200 chars + "..."
        assert len(references[0].content_preview) <= 210


class TestQAServiceRunQAModel:
    """Tests for QA model execution."""

    @pytest.mark.asyncio
    async def test_run_qa_model_empty_context(self, qa_service):
        """Test QA model with empty context."""
        answer, confidence = await qa_service._run_qa_model(
            "What is the total?", ""
        )
        
        assert "no context" in answer.lower()
        assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_run_qa_model_success(self, qa_service, mock_model_loader):
        """Test successful QA model execution."""
        answer, confidence = await qa_service._run_qa_model(
            "What is the total?", "The total is $100."
        )
        
        assert answer == "Test answer"
        assert confidence == 0.85

    @pytest.mark.asyncio
    async def test_run_qa_model_low_confidence(self, qa_service, mock_model_loader):
        """Test QA model with low confidence answer."""
        mock_model_loader.qa_pipeline.return_value = {
            "answer": "",
            "score": 0.001,
        }
        
        answer, confidence = await qa_service._run_qa_model(
            "What is the total?", "Unrelated content."
        )
        
        assert "couldn't find" in answer.lower()


class TestQAServiceGenerativeMode:
    """Tests for generative RAG mode."""

    @pytest.fixture
    def mock_llm_model_loader(self, mock_db):
        """Create a mock model loader with LLM client (generative mode)."""
        with patch("app.services.qa_service.get_model_loader") as mock_loader:
            mock_instance = MagicMock()
            mock_instance.qa_available = True
            mock_instance.llm_available = True
            mock_instance.llm_provider = "ollama"
            
            # Mock LLM client
            mock_llm_client = AsyncMock()
            mock_llm_client.generate = AsyncMock(return_value="Generated answer from LLM")
            mock_instance.llm_client = mock_llm_client
            
            mock_loader.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_run_generative_qa_success(self, mock_db, mock_llm_model_loader):
        """Test successful generative QA execution."""
        QAService.clear_cache()
        service = QAService(mock_db)
        
        answer, confidence = await service._run_generative_qa(
            "What is the total?", "The total amount is $100."
        )
        
        assert answer == "Generated answer from LLM"
        assert 0.0 < confidence <= 1.0
        mock_llm_model_loader.llm_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_qa_model_uses_llm_when_available(self, mock_db, mock_llm_model_loader):
        """Test that _run_qa_model uses LLM when available."""
        QAService.clear_cache()
        service = QAService(mock_db)
        
        answer, confidence = await service._run_qa_model(
            "What is the total?", "The total is $100."
        )
        
        assert answer == "Generated answer from LLM"
        mock_llm_model_loader.llm_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generative_qa_fallback_on_error(self, mock_db):
        """Test that generative QA falls back to extractive on error."""
        with patch("app.services.qa_service.get_model_loader") as mock_loader:
            mock_instance = MagicMock()
            mock_instance.qa_available = True
            mock_instance.llm_available = True
            mock_instance.llm_provider = "ollama"
            
            # Mock LLM client that raises an error
            mock_llm_client = AsyncMock()
            mock_llm_client.generate = AsyncMock(side_effect=Exception("LLM error"))
            mock_instance.llm_client = mock_llm_client
            
            # Mock extractive QA pipeline
            mock_instance.qa_pipeline = MagicMock()
            mock_instance.qa_pipeline.return_value = {
                "answer": "Extractive fallback answer",
                "score": 0.75,
            }
            
            mock_loader.return_value = mock_instance
            
            QAService.clear_cache()
            service = QAService(mock_db)
            
            answer, confidence = await service._run_qa_model(
                "What is the total?", "The total is $100."
            )
            
            # Should fall back to extractive QA
            assert answer == "Extractive fallback answer"
            assert confidence == 0.75


class TestConfidenceEstimation:
    """Tests for generative confidence estimation."""

    @pytest.fixture
    def qa_service_for_confidence(self, mock_db, mock_model_loader):
        """Create a QAService for confidence tests."""
        QAService.clear_cache()
        return QAService(mock_db)

    def test_estimate_confidence_normal_answer(self, qa_service_for_confidence):
        """Test confidence estimation for a normal answer."""
        confidence = qa_service_for_confidence._estimate_generative_confidence(
            "The total amount is $100.00",
            "The invoice shows a total amount of $100.00 for services rendered."
        )
        
        assert 0.5 < confidence <= 0.95

    def test_estimate_confidence_short_answer(self, qa_service_for_confidence):
        """Test confidence estimation for a very short answer."""
        confidence = qa_service_for_confidence._estimate_generative_confidence(
            "Yes",
            "The document confirms the payment was received."
        )
        
        # Short answers should have lower confidence
        assert confidence < 0.7

    def test_estimate_confidence_uncertainty_phrase(self, qa_service_for_confidence):
        """Test confidence estimation when answer contains uncertainty."""
        confidence = qa_service_for_confidence._estimate_generative_confidence(
            "I'm not sure, but it might be $100.",
            "The total is $100."
        )
        
        # Uncertainty phrases should lower confidence
        assert confidence < 0.5

    def test_estimate_confidence_no_information(self, qa_service_for_confidence):
        """Test confidence estimation when answer indicates no information."""
        confidence = qa_service_for_confidence._estimate_generative_confidence(
            "The context doesn't contain information about the CEO.",
            "The company was founded in 2020."
        )
        
        # "doesn't contain" should lower confidence
        assert confidence < 0.5
