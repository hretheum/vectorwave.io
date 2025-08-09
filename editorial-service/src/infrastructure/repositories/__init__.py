"""
Infrastructure Repositories for Editorial Service

Repository implementations for data access.
"""
from .mock_rule_repository import MockRuleRepository

try:
    from .chromadb_rule_repository import ChromaDBRuleRepository  # type: ignore
except Exception:
    # Optional import: file may not exist in some test contexts
    ChromaDBRuleRepository = None  # type: ignore

__all__ = [
    'MockRuleRepository',
    'ChromaDBRuleRepository'
]