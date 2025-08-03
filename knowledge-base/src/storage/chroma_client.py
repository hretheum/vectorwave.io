"""Chroma DB Client - Vector Store Implementation"""

import asyncio
import uuid
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import structlog
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = structlog.get_logger()


@dataclass
class ChromaDocument:
    """Document representation for Chroma DB"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embeddings: Optional[List[float]] = None


@dataclass
class SearchResult:
    """Search result from vector store"""
    document: ChromaDocument
    score: float
    distance: float


class ChromaClient:
    """Chroma DB Client for Vector Store operations"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "crewai_knowledge",
        embedding_model: str = "all-MiniLM-L6-v2",
        similarity_metric: str = "cosine"
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.similarity_metric = similarity_metric
        
        # Initialize clients
        self._client: Optional[chromadb.HttpClient] = None
        self._collection: Optional[chromadb.Collection] = None
        self._embedding_model: Optional[SentenceTransformer] = None
        
        # Performance tracking
        self._stats = {
            "queries_total": 0,
            "documents_added": 0,
            "documents_updated": 0,
            "avg_query_time_ms": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize Chroma client and collection"""
        try:
            # Initialize HTTP client
            self._client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Test connection
            await self._test_connection()
            
            # Initialize embedding model
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
            
            # Create or get collection
            await self._setup_collection()
            
            logger.info(
                "Chroma client initialized",
                host=self.host,
                port=self.port,
                collection=self.collection_name,
                embedding_model=self.embedding_model_name
            )
            
        except Exception as e:
            logger.error(
                "Failed to initialize Chroma client",
                error=str(e),
                host=self.host,
                port=self.port
            )
            raise
    
    async def _test_connection(self) -> None:
        """Test connection to Chroma server"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self._client.heartbeat()
            )
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Chroma server: {e}")
    
    async def _setup_collection(self) -> None:
        """Create or get collection with proper configuration"""
        try:
            # Create embedding function
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model_name
            )
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            
            # Try to get existing collection first
            try:
                self._collection = await loop.run_in_executor(
                    None,
                    lambda: self._client.get_collection(
                        name=self.collection_name,
                        embedding_function=embedding_function
                    )
                )
                logger.info("Using existing collection", name=self.collection_name)
            except Exception:
                # Collection doesn't exist, create it
                self._collection = await loop.run_in_executor(
                    None,
                    lambda: self._client.create_collection(
                        name=self.collection_name,
                        embedding_function=embedding_function,
                        metadata={
                            "hnsw:space": self.similarity_metric,
                            "description": "CrewAI Knowledge Base - Vector Wave",
                            "version": "1.0.0"
                        }
                    )
                )
                logger.info("Created new collection", name=self.collection_name)
                
        except Exception as e:
            logger.error(
                "Failed to setup collection",
                error=str(e),
                collection=self.collection_name
            )
            raise
    
    async def add_documents(
        self, 
        documents: List[ChromaDocument],
        batch_size: int = 32
    ) -> None:
        """Add multiple documents to the vector store"""
        if not self._collection:
            raise RuntimeError("Client not initialized")
        
        total_docs = len(documents)
        logger.info("Adding documents to vector store", count=total_docs)
        
        try:
            # Process in batches for better performance
            for i in range(0, total_docs, batch_size):
                batch = documents[i:i + batch_size]
                await self._add_batch(batch)
                
                self._stats["documents_added"] += len(batch)
                logger.debug(
                    "Added batch to vector store",
                    batch_size=len(batch),
                    progress=f"{i + len(batch)}/{total_docs}"
                )
            
            logger.info(
                "Successfully added all documents",
                total=total_docs,
                stats=self._stats
            )
            
        except Exception as e:
            logger.error(
                "Failed to add documents",
                error=str(e),
                attempted_count=total_docs
            )
            raise
    
    async def _add_batch(self, documents: List[ChromaDocument]) -> None:
        """Add a batch of documents"""
        if not documents:
            return
        
        # Prepare data for Chroma
        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Generate embeddings if not provided
        embeddings = []
        for doc in documents:
            if doc.embeddings:
                embeddings.append(doc.embeddings)
            else:
                # Use the collection's embedding function
                embeddings = None
                break
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._collection.add(
                documents=contents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings if embeddings else None
            )
        )
    
    async def update_document(self, document: ChromaDocument) -> None:
        """Update a single document"""
        if not self._collection:
            raise RuntimeError("Client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._collection.update(
                    ids=[document.id],
                    documents=[document.content],
                    metadatas=[document.metadata],
                    embeddings=[document.embeddings] if document.embeddings else None
                )
            )
            
            self._stats["documents_updated"] += 1
            logger.debug("Updated document", doc_id=document.id)
            
        except Exception as e:
            logger.error(
                "Failed to update document",
                doc_id=document.id,
                error=str(e)
            )
            raise
    
    async def delete_document(self, doc_id: str) -> None:
        """Delete a document by ID"""
        if not self._collection:
            raise RuntimeError("Client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._collection.delete(ids=[doc_id])
            )
            
            logger.debug("Deleted document", doc_id=doc_id)
            
        except Exception as e:
            logger.error(
                "Failed to delete document",
                doc_id=doc_id,
                error=str(e)
            )
            raise
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.35,
        where: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents"""
        if not self._collection:
            raise RuntimeError("Client not initialized")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Run query in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self._collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where=where,
                    include=["documents", "metadatas", "distances"]
                )
            )
            
            # Process results
            search_results = self._process_search_results(results, score_threshold)
            
            # Update stats
            query_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            self._stats["queries_total"] += 1
            self._update_avg_query_time(query_time_ms)
            
            logger.debug(
                "Vector search completed",
                query=query[:100],  # Truncate for logging
                results_count=len(search_results),
                query_time_ms=round(query_time_ms, 2)
            )
            
            return search_results
            
        except Exception as e:
            logger.error(
                "Vector search failed",
                query=query[:100],
                error=str(e)
            )
            raise
    
    def _process_search_results(
        self, 
        raw_results: Dict[str, Any], 
        score_threshold: float
    ) -> List[SearchResult]:
        """Process raw Chroma results into SearchResult objects"""
        results = []
        
        if not raw_results["documents"] or not raw_results["documents"][0]:
            return results
        
        documents = raw_results["documents"][0]
        metadatas = raw_results["metadatas"][0]
        distances = raw_results["distances"][0]
        ids = raw_results["ids"][0]
        
        for i, (doc_id, content, metadata, distance) in enumerate(
            zip(ids, documents, metadatas, distances)
        ):
            # Convert distance to similarity score (cosine similarity)
            score = 1.0 - distance if distance is not None else 0.0
            
            # Filter by threshold
            if score >= score_threshold:
                chroma_doc = ChromaDocument(
                    id=doc_id,
                    content=content,
                    metadata=metadata or {}
                )
                
                results.append(SearchResult(
                    document=chroma_doc,
                    score=score,
                    distance=distance
                ))
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _update_avg_query_time(self, query_time_ms: float) -> None:
        """Update average query time using exponential moving average"""
        alpha = 0.1  # Smoothing factor
        if self._stats["avg_query_time_ms"] == 0:
            self._stats["avg_query_time_ms"] = query_time_ms
        else:
            self._stats["avg_query_time_ms"] = (
                alpha * query_time_ms + 
                (1 - alpha) * self._stats["avg_query_time_ms"]
            )
    
    async def get_document(self, doc_id: str) -> Optional[ChromaDocument]:
        """Get a document by ID"""
        if not self._collection:
            raise RuntimeError("Client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self._collection.get(
                    ids=[doc_id],
                    include=["documents", "metadatas"]
                )
            )
            
            if results["documents"] and results["documents"][0]:
                return ChromaDocument(
                    id=doc_id,
                    content=results["documents"][0],
                    metadata=results["metadatas"][0] or {}
                )
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to get document",
                doc_id=doc_id,
                error=str(e)
            )
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if not self._collection:
            raise RuntimeError("Client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            count = await loop.run_in_executor(
                None,
                lambda: self._collection.count()
            )
            
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model_name,
                "similarity_metric": self.similarity_metric,
                **self._stats
            }
            
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test connection
            await self._test_connection()
            
            # Get basic stats
            stats = await self.get_collection_stats()
            
            return {
                "status": "healthy",
                "connection": "ok",
                "collection_exists": self._collection is not None,
                "stats": stats
            }
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }
    
    async def close(self) -> None:
        """Close connections and cleanup"""
        try:
            # Chroma HTTP client doesn't need explicit closing
            # But we can reset our references
            self._collection = None
            self._client = None
            
            logger.info("Chroma client closed")
            
        except Exception as e:
            logger.error("Error closing Chroma client", error=str(e))