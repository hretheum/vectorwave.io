"""Unit tests for ChromaClient"""

import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from src.storage.chroma_client import ChromaClient, ChromaDocument, SearchResult


@pytest.mark.unit
class TestChromaClient:
    """Test ChromaClient functionality"""
    
    @pytest.fixture
    def chroma_client(self):
        """Create ChromaClient instance for testing"""
        return ChromaClient(
            host="localhost",
            port=8000,
            collection_name="test_collection",
            embedding_model="all-MiniLM-L6-v2",
            similarity_metric="cosine"
        )
    
    @pytest.fixture
    def mock_chromadb_client(self):
        """Create mock ChromaDB HTTP client"""
        mock_client = MagicMock()
        mock_client.heartbeat.return_value = None
        return mock_client
    
    @pytest.fixture
    def mock_collection(self):
        """Create mock ChromaDB collection"""
        mock_collection = MagicMock()
        mock_collection.add.return_value = None
        mock_collection.update.return_value = None
        mock_collection.delete.return_value = None
        mock_collection.get.return_value = {
            "documents": [],
            "metadatas": []
        }
        mock_collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        mock_collection.count.return_value = 0
        return mock_collection
    
    @pytest.fixture
    def mock_sentence_transformer(self):
        """Create mock SentenceTransformer"""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]  # Mock embedding
        return mock_model
    
    def test_initialization_parameters(self, chroma_client):
        """Test ChromaClient initialization parameters"""
        assert chroma_client.host == "localhost"
        assert chroma_client.port == 8000
        assert chroma_client.collection_name == "test_collection"
        assert chroma_client.embedding_model_name == "all-MiniLM-L6-v2"
        assert chroma_client.similarity_metric == "cosine"
        
        assert chroma_client._client is None
        assert chroma_client._collection is None
        assert chroma_client._embedding_model is None
        
        # Check initial stats
        expected_stats = {
            "queries_total": 0,
            "documents_added": 0,
            "documents_updated": 0,
            "avg_query_time_ms": 0.0
        }
        assert chroma_client._stats == expected_stats
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, chroma_client, mock_chromadb_client, 
                                        mock_collection, mock_sentence_transformer):
        """Test successful initialization"""
        with patch('chromadb.HttpClient', return_value=mock_chromadb_client), \
             patch('sentence_transformers.SentenceTransformer', return_value=mock_sentence_transformer), \
             patch('chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction') as mock_embedding_func:
            
            # Mock collection creation
            mock_chromadb_client.get_collection.side_effect = Exception("Collection not found")
            mock_chromadb_client.create_collection.return_value = mock_collection
            
            await chroma_client.initialize()
            
            assert chroma_client._client == mock_chromadb_client
            assert chroma_client._collection == mock_collection
            assert chroma_client._embedding_model == mock_sentence_transformer
            
            # Verify heartbeat was called
            mock_chromadb_client.heartbeat.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_existing_collection(self, chroma_client, mock_chromadb_client, 
                                                    mock_collection, mock_sentence_transformer):
        """Test initialization with existing collection"""
        with patch('chromadb.HttpClient', return_value=mock_chromadb_client), \
             patch('sentence_transformers.SentenceTransformer', return_value=mock_sentence_transformer), \
             patch('chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction'):
            
            # Mock existing collection
            mock_chromadb_client.get_collection.return_value = mock_collection
            
            await chroma_client.initialize()
            
            # Should use existing collection, not create new one
            mock_chromadb_client.get_collection.assert_called_once()
            mock_chromadb_client.create_collection.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_initialization_connection_failure(self, chroma_client):
        """Test initialization with connection failure"""
        with patch('chromadb.HttpClient') as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.heartbeat.side_effect = Exception("Connection failed")
            
            with pytest.raises(ConnectionError, match="Cannot connect to Chroma server"):
                await chroma_client.initialize()
    
    @pytest.mark.asyncio
    async def test_add_documents_success(self, chroma_client, mock_collection, sample_documents):
        """Test successful document addition"""
        chroma_client._collection = mock_collection
        
        await chroma_client.add_documents(sample_documents)
        
        # Should call add on collection
        assert mock_collection.add.call_count == 1  # 5 docs in 1 batch (batch_size=32)
        assert chroma_client._stats["documents_added"] == 5
    
    @pytest.mark.asyncio
    async def test_add_documents_not_initialized(self, chroma_client, sample_documents):
        """Test document addition without initialization"""
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await chroma_client.add_documents(sample_documents)
    
    @pytest.mark.asyncio
    async def test_add_documents_with_embeddings(self, chroma_client, mock_collection):
        """Test adding documents with pre-computed embeddings"""
        chroma_client._collection = mock_collection
        
        doc_with_embeddings = ChromaDocument(
            id="embed_doc",
            content="Document with embeddings",
            metadata={"type": "test"},
            embeddings=[0.1, 0.2, 0.3, 0.4]
        )
        
        await chroma_client.add_documents([doc_with_embeddings])
        
        # Should pass embeddings to Chroma
        mock_collection.add.assert_called_once()
        call_args = mock_collection.add.call_args
        assert call_args[1]["embeddings"] == [[0.1, 0.2, 0.3, 0.4]]
    
    @pytest.mark.asyncio
    async def test_add_documents_batch_processing(self, chroma_client, mock_collection):
        """Test batch processing of documents"""
        chroma_client._collection = mock_collection
        
        # Create more documents than batch size
        documents = []
        for i in range(70):  # More than default batch size of 32
            doc = ChromaDocument(
                id=f"batch_doc_{i}",
                content=f"Batch document {i}",
                metadata={"batch": i // 32}
            )
            documents.append(doc)
        
        await chroma_client.add_documents(documents, batch_size=32)
        
        # Should be called in 3 batches: 32, 32, 6
        assert mock_collection.add.call_count == 3
        assert chroma_client._stats["documents_added"] == 70
    
    @pytest.mark.asyncio
    async def test_update_document_success(self, chroma_client, mock_collection, sample_document):
        """Test successful document update"""
        chroma_client._collection = mock_collection
        
        await chroma_client.update_document(sample_document)
        
        mock_collection.update.assert_called_once()
        assert chroma_client._stats["documents_updated"] == 1
    
    @pytest.mark.asyncio
    async def test_update_document_not_initialized(self, chroma_client, sample_document):
        """Test document update without initialization"""
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await chroma_client.update_document(sample_document)
    
    @pytest.mark.asyncio
    async def test_delete_document_success(self, chroma_client, mock_collection):
        """Test successful document deletion"""
        chroma_client._collection = mock_collection
        
        await chroma_client.delete_document("test_doc_id")
        
        mock_collection.delete.assert_called_once_with(ids=["test_doc_id"])
    
    @pytest.mark.asyncio
    async def test_delete_document_not_initialized(self, chroma_client):
        """Test document deletion without initialization"""
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await chroma_client.delete_document("test_doc_id")
    
    @pytest.mark.asyncio
    async def test_search_success(self, chroma_client, mock_collection):
        """Test successful search operation"""
        chroma_client._collection = mock_collection
        
        # Mock search results
        mock_collection.query.return_value = {
            "documents": [["Document 1", "Document 2"]],
            "metadatas": [[{"title": "Doc 1"}, {"title": "Doc 2"}]],
            "distances": [[0.1, 0.3]],
            "ids": [["doc1", "doc2"]]
        }
        
        results = await chroma_client.search(
            query="test query",
            limit=5,
            score_threshold=0.5
        )
        
        assert len(results) == 2
        assert results[0].document.content == "Document 1"
        assert results[0].score == 0.9  # 1.0 - 0.1 distance
        assert results[1].document.content == "Document 2"
        assert results[1].score == 0.7  # 1.0 - 0.3 distance
        
        assert chroma_client._stats["queries_total"] == 1
        assert chroma_client._stats["avg_query_time_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, chroma_client, mock_collection):
        """Test search with metadata filters"""
        chroma_client._collection = mock_collection
        
        filters = {"category": "ai", "priority": {"$gte": 1}}
        
        await chroma_client.search(
            query="filtered query",
            where=filters
        )
        
        mock_collection.query.assert_called_once()
        call_args = mock_collection.query.call_args
        assert call_args[1]["where"] == filters
    
    @pytest.mark.asyncio
    async def test_search_score_threshold_filtering(self, chroma_client, mock_collection):
        """Test that search results are filtered by score threshold"""
        chroma_client._collection = mock_collection
        
        # Mock results with varying distances
        mock_collection.query.return_value = {
            "documents": [["Good Doc", "Bad Doc"]],
            "metadatas": [[{"title": "Good"}, {"title": "Bad"}]],
            "distances": [[0.1, 0.8]],  # Scores: 0.9, 0.2
            "ids": [["good", "bad"]]
        }
        
        results = await chroma_client.search(
            query="test query",
            score_threshold=0.5  # Should filter out second result
        )
        
        assert len(results) == 1
        assert results[0].document.id == "good"
        assert results[0].score == 0.9
    
    @pytest.mark.asyncio
    async def test_search_empty_results(self, chroma_client, mock_collection):
        """Test search with no results"""
        chroma_client._collection = mock_collection
        
        # Mock empty results
        mock_collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        
        results = await chroma_client.search("no results query")
        
        assert len(results) == 0
        assert chroma_client._stats["queries_total"] == 1
    
    @pytest.mark.asyncio
    async def test_search_not_initialized(self, chroma_client):
        """Test search without initialization"""
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await chroma_client.search("test query")
    
    @pytest.mark.asyncio
    async def test_get_document_success(self, chroma_client, mock_collection):
        """Test successful document retrieval"""
        chroma_client._collection = mock_collection
        
        mock_collection.get.return_value = {
            "documents": ["Document content"],
            "metadatas": [{"title": "Test Doc"}]
        }
        
        document = await chroma_client.get_document("test_doc_id")
        
        assert document is not None
        assert document.id == "test_doc_id"
        assert document.content == "Document content"
        assert document.metadata == {"title": "Test Doc"}
    
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, chroma_client, mock_collection):
        """Test getting nonexistent document"""
        chroma_client._collection = mock_collection
        
        mock_collection.get.return_value = {
            "documents": [],
            "metadatas": []
        }
        
        document = await chroma_client.get_document("nonexistent_doc")
        
        assert document is None
    
    @pytest.mark.asyncio
    async def test_get_collection_stats(self, chroma_client, mock_collection):
        """Test getting collection statistics"""
        chroma_client._collection = mock_collection
        mock_collection.count.return_value = 150
        
        # Set some stats
        chroma_client._stats["queries_total"] = 25
        chroma_client._stats["documents_added"] = 100
        
        stats = await chroma_client.get_collection_stats()
        
        assert stats["total_documents"] == 150
        assert stats["collection_name"] == "test_collection"
        assert stats["embedding_model"] == "all-MiniLM-L6-v2"
        assert stats["similarity_metric"] == "cosine"
        assert stats["queries_total"] == 25
        assert stats["documents_added"] == 100
    
    @pytest.mark.asyncio
    async def test_get_collection_stats_not_initialized(self, chroma_client):
        """Test getting stats without initialization"""
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await chroma_client.get_collection_stats()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, chroma_client, mock_collection):
        """Test successful health check"""
        chroma_client._collection = mock_collection
        chroma_client._client = MagicMock()
        chroma_client._client.heartbeat.return_value = None
        
        mock_collection.count.return_value = 50
        
        health = await chroma_client.health_check()
        
        assert health["status"] == "healthy"
        assert health["connection"] == "ok"
        assert health["collection_exists"] is True
        assert "stats" in health
    
    @pytest.mark.asyncio
    async def test_health_check_connection_failure(self, chroma_client):
        """Test health check with connection failure"""
        chroma_client._client = MagicMock()
        chroma_client._client.heartbeat.side_effect = Exception("Connection lost")
        
        health = await chroma_client.health_check()
        
        assert health["status"] == "unhealthy"
        assert health["connection"] == "failed"
        assert "Connection lost" in health["error"]
    
    @pytest.mark.asyncio
    async def test_close(self, chroma_client):
        """Test closing client connections"""
        chroma_client._client = MagicMock()
        chroma_client._collection = MagicMock()
        
        await chroma_client.close()
        
        assert chroma_client._collection is None
        assert chroma_client._client is None
    
    def test_process_search_results_empty(self, chroma_client):
        """Test processing empty search results"""
        raw_results = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        
        results = chroma_client._process_search_results(raw_results, 0.5)
        
        assert len(results) == 0
    
    def test_process_search_results_with_data(self, chroma_client):
        """Test processing search results with data"""
        raw_results = {
            "documents": [["Doc 1", "Doc 2", "Doc 3"]],
            "metadatas": [[{"title": "T1"}, {"title": "T2"}, {"title": "T3"}]],
            "distances": [[0.1, 0.4, 0.7]],
            "ids": [["id1", "id2", "id3"]]
        }
        
        results = chroma_client._process_search_results(raw_results, 0.5)
        
        # Should filter out the third result (score 0.3 < 0.5)
        assert len(results) == 2
        
        # Results should be sorted by score (highest first)
        assert results[0].score == 0.9  # 1.0 - 0.1
        assert results[1].score == 0.6  # 1.0 - 0.4
        
        assert results[0].document.id == "id1"
        assert results[0].document.content == "Doc 1"
        assert results[0].document.metadata == {"title": "T1"}
    
    def test_update_avg_query_time(self, chroma_client):
        """Test average query time calculation"""
        # First query
        chroma_client._update_avg_query_time(100.0)
        assert chroma_client._stats["avg_query_time_ms"] == 100.0
        
        # Second query (should use exponential moving average)
        chroma_client._update_avg_query_time(200.0)
        expected = 0.1 * 200.0 + 0.9 * 100.0  # alpha=0.1
        assert chroma_client._stats["avg_query_time_ms"] == expected
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, chroma_client, mock_collection):
        """Test error handling in search operation"""
        chroma_client._collection = mock_collection
        mock_collection.query.side_effect = Exception("Search error")
        
        with pytest.raises(Exception, match="Search error"):
            await chroma_client.search("error query")
    
    @pytest.mark.asyncio
    async def test_add_documents_error_handling(self, chroma_client, mock_collection, sample_documents):
        """Test error handling in add documents operation"""
        chroma_client._collection = mock_collection
        mock_collection.add.side_effect = Exception("Add error")
        
        with pytest.raises(Exception, match="Add error"):
            await chroma_client.add_documents(sample_documents)


@pytest.mark.unit
class TestChromaDocument:
    """Test ChromaDocument dataclass"""
    
    def test_creation(self):
        """Test creating ChromaDocument"""
        doc = ChromaDocument(
            id="test_id",
            content="Test content",
            metadata={"key": "value"},
            embeddings=[0.1, 0.2, 0.3]
        )
        
        assert doc.id == "test_id"
        assert doc.content == "Test content"
        assert doc.metadata == {"key": "value"}
        assert doc.embeddings == [0.1, 0.2, 0.3]
    
    def test_creation_without_embeddings(self):
        """Test creating ChromaDocument without embeddings"""
        doc = ChromaDocument(
            id="test_id",
            content="Test content",
            metadata={"key": "value"}
        )
        
        assert doc.embeddings is None


@pytest.mark.unit
class TestSearchResult:
    """Test SearchResult dataclass"""
    
    def test_creation(self, sample_document):
        """Test creating SearchResult"""
        result = SearchResult(
            document=sample_document,
            score=0.85,
            distance=0.15
        )
        
        assert result.document == sample_document
        assert result.score == 0.85
        assert result.distance == 0.15


@pytest.mark.unit
@pytest.mark.performance
class TestChromaClientPerformance:
    """Performance tests for ChromaClient"""
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, chroma_client, mock_collection):
        """Test performance of batch processing"""
        chroma_client._collection = mock_collection
        
        # Create large number of documents
        documents = []
        for i in range(1000):
            doc = ChromaDocument(
                id=f"perf_doc_{i}",
                content=f"Performance test document {i} with some content",
                metadata={"index": i, "category": f"cat_{i % 10}"}
            )
            documents.append(doc)
        
        import time
        start_time = time.time()
        
        await chroma_client.add_documents(documents, batch_size=50)
        
        end_time = time.time()
        
        # Should complete reasonably quickly
        assert (end_time - start_time) < 1.0  # 1 second for 1000 docs
        assert chroma_client._stats["documents_added"] == 1000
    
    def test_result_processing_performance(self, chroma_client):
        """Test performance of search result processing"""
        # Create large result set
        num_results = 10000
        raw_results = {
            "documents": [[f"Document {i}" for i in range(num_results)]],
            "metadatas": [[{"title": f"Title {i}"} for i in range(num_results)]],
            "distances": [[i / num_results for i in range(num_results)]],
            "ids": [[f"id_{i}" for i in range(num_results)]]
        }
        
        import time
        start_time = time.time()
        
        results = chroma_client._process_search_results(raw_results, 0.1)
        
        end_time = time.time()
        
        # Should process results quickly
        assert (end_time - start_time) < 0.5  # 500ms for 10k results
        assert len(results) > 0