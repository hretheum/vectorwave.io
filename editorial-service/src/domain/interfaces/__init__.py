"""
Domain Interfaces for Editorial Service

Abstract interfaces defining contracts for the domain layer.
"""
from .validation_strategy import IValidationStrategy
from .rule_repository import IRuleRepository

__all__ = [
    'IValidationStrategy',
    'IRuleRepository'
]