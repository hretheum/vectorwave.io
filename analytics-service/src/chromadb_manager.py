"""
ChromaDB Manager for Analytics Service
Handles all ChromaDB operations for multi-platform analytics data
"""

import logging
import chromadb
from chromadb.config import Settings
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """ChromaDB health status"""
    status: str
    collections_count: int
    error: Optional[str] = None


class ChromaDBManager:
    """
    ChromaDB integration manager for Analytics Service
    Implements the repository layer of Clean Architecture
    """
    
    def __init__(self, chromadb_url: str):
        self.chromadb_url = chromadb_url
        self.client = None
        self.collections = {}
        
        # Analytics collections schema
        self.COLLECTIONS_SCHEMA = {
            "platform_analytics": {
                "description": "Raw analytics data from all platforms",
                "metadata_schema": {
                    "entry_id": str,
                    "publication_id": str,
                    "platform": str,  # ghost, twitter, linkedin, beehiiv
                    "collection_method": str,  # api, proxy, manual, csv
                    "metrics": dict,
                    "quality_score": float,
                    "collected_at": str,
                    "processed": bool
                }
            },
            "platform_configurations": {
                "description": "Platform-specific collection configurations",
                "metadata_schema": {
                    "config_id": str,
                    "platform": str,
                    "collection_method": str,
                    "api_credentials_hash": str,
                    "collection_frequency": str,
                    "enabled_metrics": list,
                    "created_by": str,
                    "created_at": str
                }
            },
            "analytics_insights": {
                "description": "Generated insights and recommendations",
                "metadata_schema": {
                    "insight_id": str,
                    "user_id": str,
                    "time_period": str,
                    "platforms_analyzed": list,
                    "key_insights": list,
                    "recommendations": list,
                    "data_quality_score": float,
                    "generated_at": str
                }
            }
        }
    
    async def initialize(self):
        """Initialize ChromaDB connection and collections"""
        try:
            logger.info(f"🔗 Connecting to ChromaDB: {self.chromadb_url}")
            
            # Parse ChromaDB URL
            if self.chromadb_url.startswith("http://"):
                host_port = self.chromadb_url.replace("http://", "")
                host, port = host_port.split(":")
                port = int(port)
            else:
                host, port = "localhost", 8000
            
            # Initialize ChromaDB client
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(allow_reset=False)
            )
            
            # Test connection
            heartbeat = self.client.heartbeat()
            logger.info(f"✅ ChromaDB connection successful: {heartbeat}")
            
            # Initialize collections
            await self._initialize_collections()
            
            logger.info("🗃️ Analytics collections initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {e}")
            raise
    
    async def _initialize_collections(self):
        """Initialize all required analytics collections"""
        for collection_name, schema in self.COLLECTIONS_SCHEMA.items():
            try:
                # Try to get existing collection
                collection = self.client.get_collection(name=collection_name)
                logger.info(f"📋 Found existing collection: {collection_name}")
                
            except Exception:
                # Collection doesn't exist, create it
                logger.info(f"🆕 Creating collection: {collection_name}")
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": schema["description"]}
                )
            
            self.collections[collection_name] = collection
            
            # Log collection stats
            collection_count = collection.count()
            logger.info(f"📊 {collection_name}: {collection_count} documents")
    
    async def health_check(self) -> HealthStatus:
        """Check ChromaDB health and collection status"""
        try:
            if not self.client:
                return HealthStatus(status="disconnected", collections_count=0, error="No client")
            
            # Test heartbeat
            heartbeat = self.client.heartbeat()
            
            # Count collections
            collections_count = len(self.collections)
            
            return HealthStatus(
                status="connected",
                collections_count=collections_count
            )
            
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return HealthStatus(
                status="error",
                collections_count=0,
                error=str(e)
            )
    
    async def store_analytics_data(self, entry_id: str, platform: str, 
                                   collection_method: str, metrics: Dict[str, Any], 
                                   publication_id: str, quality_score: float,
                                   user_id: str, additional_metadata: Dict = None) -> bool:
        """Store analytics data in platform_analytics collection"""
        try:
            collection = self.collections["platform_analytics"]
            
            # Prepare document content
            content = f"{platform} analytics for publication {publication_id}"
            
            # Prepare metadata
            metadata = {
                "entry_id": entry_id,
                "publication_id": publication_id,
                "platform": platform,
                "collection_method": collection_method,
                "metrics": metrics,
                "quality_score": quality_score,
                "collected_at": datetime.now().isoformat(),
                "submitted_by": user_id,
                "processed": False
            }
            
            # Add additional metadata if provided
            if additional_metadata:
                metadata.update(additional_metadata)
            
            # Store in ChromaDB
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[entry_id]
            )
            
            logger.info(f"✅ Stored analytics data: {entry_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store analytics data: {e}")
            return False
    
    async def store_platform_configuration(self, platform: str, config: Dict[str, Any],
                                          response: Dict[str, Any], user_id: str) -> bool:
        """Store platform configuration in platform_configurations collection"""
        try:
            collection = self.collections["platform_configurations"]
            
            config_id = f"config_{platform}_{uuid.uuid4().hex[:8]}"
            
            # Prepare document content
            content = f"Configuration for {platform} platform analytics"
            
            # Prepare metadata (without sensitive data)
            metadata = {
                "config_id": config_id,
                "platform": platform,
                "collection_method": config.get("collection_method"),
                "api_credentials_hash": "hashed" if config.get("api_credentials") else None,
                "collection_frequency": config.get("collection_frequency"),
                "enabled_metrics": config.get("enabled_metrics", []),
                "created_by": user_id,
                "created_at": datetime.now().isoformat(),
                "status": response.get("status"),
                "limitations": response.get("limitations", [])
            }
            
            # Store in ChromaDB
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[config_id]
            )
            
            logger.info(f"✅ Stored platform configuration: {config_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store platform configuration: {e}")
            return False
    
    async def query_user_analytics(self, user_id: str, platforms: Optional[List[str]] = None,
                                  time_period: str = "30d") -> List[Dict[str, Any]]:
        """Query analytics data for a specific user"""
        try:
            collection = self.collections["platform_analytics"]
            
            # Build where filter
            where_filter = {"submitted_by": user_id}
            if platforms:
                where_filter["platform"] = {"$in": platforms}
            
            # Query ChromaDB
            results = collection.query(
                where=where_filter,
                n_results=1000  # Reasonable limit
            )
            
            logger.info(f"📊 Found {len(results['documents'])} analytics records for user {user_id}")
            
            # Combine documents with metadata
            analytics_data = []
            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i] if i < len(results["metadatas"]) else {}
                analytics_data.append({
                    "document": doc,
                    "metadata": metadata,
                    "id": results["ids"][i] if i < len(results["ids"]) else None
                })
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"❌ Failed to query user analytics: {e}")
            return []
    
    async def store_generated_insights(self, user_id: str, insights: Dict[str, Any]) -> bool:
        """Store generated insights in analytics_insights collection"""
        try:
            collection = self.collections["analytics_insights"]
            
            insight_id = f"insights_{user_id}_{uuid.uuid4().hex[:8]}"
            
            # Prepare document content
            content = f"Analytics insights for user {user_id}"
            
            # Prepare metadata
            metadata = {
                "insight_id": insight_id,
                "user_id": user_id,
                "time_period": insights.get("time_period"),
                "platforms_analyzed": insights.get("platforms_analyzed", []),
                "key_insights": insights.get("key_insights", []),
                "recommendations": insights.get("recommendations", []),
                "data_quality_score": insights.get("data_quality_score", 0.0),
                "generated_at": datetime.now().isoformat()
            }
            
            # Store in ChromaDB
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[insight_id]
            )
            
            logger.info(f"✅ Stored generated insights: {insight_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store insights: {e}")
            return False
    
    async def get_platform_configurations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's platform configurations"""
        try:
            collection = self.collections["platform_configurations"]
            
            results = collection.query(
                where={"created_by": user_id},
                n_results=100
            )
            
            configurations = []
            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i] if i < len(results["metadatas"]) else {}
                configurations.append({
                    "document": doc,
                    "metadata": metadata,
                    "id": results["ids"][i] if i < len(results["ids"]) else None
                })
            
            return configurations
            
        except Exception as e:
            logger.error(f"❌ Failed to get platform configurations: {e}")
            return []
    
    async def close(self):
        """Close ChromaDB connection"""
        if self.client:
            logger.info("👋 Closing ChromaDB connection")
            # ChromaDB HttpClient doesn't need explicit closing
            self.client = None
            self.collections = {}