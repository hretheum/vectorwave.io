"""
Application Strategies for Editorial Service

Concrete implementations of validation strategies.
"""
from .comprehensive_strategy import ComprehensiveStrategy
from .selective_strategy import SelectiveStrategy

__all__ = [
    'ComprehensiveStrategy',
    'SelectiveStrategy'
]