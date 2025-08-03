"""Unit tests for ChromaClient"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.storage.chroma_client import ChromaClient, ChromaDocument, SearchResult


class TestChromaClient:
    """Test ChromaClient functionality"""
    
    @pytest.fixture
    def chroma_client(self):
        """Create ChromaClient instance for testing"""
        return ChromaClient(
            host="localhost",
            port=8000,
            collection_name="test_collection"
        )
    
    @pytest.fixture
    def sample_document(self):
        """Create sample ChromaDocument for testing"""
        return ChromaDocument(
            id="test_doc_1",
            content="This is a test document about CrewAI agents and workflows.",
            metadata={
                "title": "Test Document",
                "source_type": "markdown",
                "category": "testing",
                "tags": ["test", "crewai"]
            }
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, chroma_client):
        """Test ChromaClient initialization"""
        # Mock the HTTP client and collection setup
        with patch('chromadb.HttpClient') as mock_http_client, \
             patch('sentence_transformers.SentenceTransformer') as mock_transformer:
            
            mock_client_instance = MagicMock()
            mock_http_client.return_value = mock_client_instance
            mock_client_instance.heartbeat.return_value = True
            
            mock_collection = MagicMock()
            mock_client_instance.get_collection.side_effect = Exception("Not found")
            mock_client_instance.create_collection.return_value = mock_collection
            
            # Test initialization
            await chroma_client.initialize()
            
            # Verify calls
            mock_http_client.assert_called_once()
            mock_transformer.assert_called_once_with("all-MiniLM-L6-v2")
            mock_client_instance.create_collection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_documents(self, chroma_client, sample_document):
        """Test adding documents to vector store"""
        # Setup mocks
        chroma_client._collection = MagicMock()
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock()
            
            # Test adding documents
            await chroma_client.add_documents([sample_document])
            
            # Verify executor was called
            mock_loop.return_value.run_in_executor.assert_called()
    
    @pytest.mark.asyncio
    async def test_search(self, chroma_client):
        """Test vector search functionality"""
        # Setup mocks
        chroma_client._collection = MagicMock()
        
        # Mock query results
        mock_results = {
            "documents": [["Test document content"]],
            "metadatas": [[{"title": "Test", "source_type": "test"}]],
            "distances": [[0.2]],
            "ids": [["test_id"]]
        }
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_results)
            
            # Test search
            results = await chroma_client.search(
                query="test query",
                limit=5,
                score_threshold=0.3
            )
            
            # Verify results
            assert len(results) == 1
            assert isinstance(results[0], SearchResult)
            assert results[0].document.content == "Test document content"
            assert results[0].score == 0.8  # 1.0 - 0.2 distance
    
    @pytest.mark.asyncio
    async def test_search_with_threshold_filtering(self, chroma_client):
        """Test that search filters results by score threshold"""
        chroma_client._collection = MagicMock()
        
        # Mock results with low similarity (high distance)
        mock_results = {
            "documents": [["Low relevance document"]],
            "metadatas": [[{"title": "Low Relevance"}]],
            "distances": [[0.8]],  # High distance = low similarity
            "ids": [["low_relevance_id"]]
        }
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_results)
            
            # Test search with high threshold
            results = await chroma_client.search(
                query="test query",
                score_threshold=0.5  # Score would be 0.2 (1.0 - 0.8)
            )
            
            # Should be filtered out
            assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_update_document(self, chroma_client, sample_document):
        """Test document update functionality"""
        chroma_client._collection = MagicMock()
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock()
            
            # Test update
            await chroma_client.update_document(sample_document)
            
            # Verify executor was called
            mock_loop.return_value.run_in_executor.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_document(self, chroma_client):
        """Test document deletion"""
        chroma_client._collection = MagicMock()
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock()
            
            # Test delete
            await chroma_client.delete_document("test_doc_id")
            
            # Verify executor was called
            mock_loop.return_value.run_in_executor.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_collection_stats(self, chroma_client):
        """Test getting collection statistics"""
        chroma_client._collection = MagicMock()
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=100)
            
            # Test stats
            stats = await chroma_client.get_collection_stats()
            
            # Verify stats structure
            assert "total_documents" in stats
            assert stats["total_documents"] == 100
            assert "collection_name" in stats
            assert "embedding_model" in stats
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, chroma_client):
        """Test health check when system is healthy"""
        chroma_client._client = MagicMock()
        chroma_client._collection = MagicMock()
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(side_effect=[None, 50])
            
            # Test health check
            health = await chroma_client.health_check()
            
            # Verify healthy status
            assert health["status"] == "healthy"
            assert health["connection"] == "ok"
            assert health["collection_exists"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, chroma_client):
        """Test health check when system is unhealthy"""
        chroma_client._client = MagicMock()
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            
            # Test health check
            health = await chroma_client.health_check()
            
            # Verify unhealthy status
            assert health["status"] == "unhealthy"
            assert "error" in health
    
    @pytest.mark.asyncio
    async def test_client_not_initialized_error(self, chroma_client):
        """Test that operations fail when client is not initialized"""
        # Don't initialize the client
        
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await chroma_client.search("test query")
        
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await chroma_client.add_documents([])
    
    def test_process_search_results_empty(self, chroma_client):
        """Test processing empty search results"""
        empty_results = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        
        processed = chroma_client._process_search_results(empty_results, 0.5)
        assert processed == []
    
    def test_process_search_results_with_data(self, chroma_client):
        """Test processing search results with actual data"""
        results = {
            "documents": [["Doc 1", "Doc 2"]],
            "metadatas": [[{"title": "Title 1"}, {"title": "Title 2"}]],
            "distances": [[0.1, 0.3]],
            "ids": [["id1", "id2"]]
        }
        
        processed = chroma_client._process_search_results(results, 0.5)
        
        # Should have 2 results (both above threshold)
        assert len(processed) == 2
        
        # Should be sorted by score (highest first)
        assert processed[0].score > processed[1].score
        assert processed[0].document.id == "id1"  # Higher score (0.9)
        assert processed[1].document.id == "id2"  # Lower score (0.7)
    
    def test_update_avg_query_time(self, chroma_client):
        """Test average query time calculation"""
        # First query
        chroma_client._update_avg_query_time(100.0)
        assert chroma_client._stats["avg_query_time_ms"] == 100.0
        
        # Second query (should use exponential moving average)
        chroma_client._update_avg_query_time(200.0)
        expected = 0.1 * 200.0 + 0.9 * 100.0  # alpha=0.1
        assert chroma_client._stats["avg_query_time_ms"] == expected