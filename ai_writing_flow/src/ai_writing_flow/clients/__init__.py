"""
Vector Wave AI Writing Flow Clients
HTTP clients for inter-service communication
"""

from .editorial_client import EditorialServiceClient
from .topic_manager_client import TopicManagerClient

__all__ = ["EditorialServiceClient", "TopicManagerClient"]