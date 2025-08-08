"""
Unit Tests: ValidationStrategyFactory
Tests the factory pattern implementation for creating validation strategies.
"""
import pytest
from unittest.mock import Mock

from src.application.services.validation_strategy_factory import ValidationStrategyFactory
from src.application.strategies import ComprehensiveStrategy, SelectiveStrategy
from src.domain.interfaces import IRuleRepository


class TestValidationStrategyFactory:
    """Test suite for ValidationStrategyFactory"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock rule repository for testing"""
        return Mock(spec=IRuleRepository)
    
    @pytest.fixture
    def factory(self, mock_repository):
        """ValidationStrategyFactory instance"""
        return ValidationStrategyFactory(mock_repository)
    
    def test_create_comprehensive_strategy(self, factory):
        """Test: ValidationStrategyFactory.create('comprehensive') returns ComprehensiveStrategy"""
        # Act
        strategy = factory.create('comprehensive')
        
        # Assert
        assert isinstance(strategy, ComprehensiveStrategy)
        assert strategy.get_strategy_name() == "Comprehensive"
        assert strategy.get_workflow_name() == "Kolegium"
        assert strategy.get_expected_rule_count_range() == (8, 12)
    
    def test_create_selective_strategy(self, factory):
        """Test: ValidationStrategyFactory.create('selective') returns SelectiveStrategy"""
        # Act
        strategy = factory.create('selective')
        
        # Assert
        assert isinstance(strategy, SelectiveStrategy)
        assert strategy.get_strategy_name() == "Selective"
        assert strategy.get_workflow_name() == "AI Writing Flow"
        assert strategy.get_expected_rule_count_range() == (3, 4)
    
    def test_both_strategies_implement_same_interface(self, factory):
        """Test: Both strategies implement same IValidationStrategy interface"""
        # Act
        comprehensive = factory.create('comprehensive')
        selective = factory.create('selective')
        
        # Assert - Both should have same interface methods
        interface_methods = [
            'validate', 'get_expected_rule_count_range', 
            'supports_request', 'get_strategy_name', 'get_workflow_name'
        ]
        
        for method in interface_methods:
            assert hasattr(comprehensive, method)
            assert hasattr(selective, method)
            assert callable(getattr(comprehensive, method))
            assert callable(getattr(selective, method))
    
    def test_create_case_insensitive(self, factory):
        """Test: Factory handles case-insensitive mode strings"""
        # Act & Assert
        assert isinstance(factory.create('COMPREHENSIVE'), ComprehensiveStrategy)
        assert isinstance(factory.create('Comprehensive'), ComprehensiveStrategy)
        assert isinstance(factory.create('SELECTIVE'), SelectiveStrategy)
        assert isinstance(factory.create('Selective'), SelectiveStrategy)
    
    def test_create_invalid_mode_raises_error(self, factory):
        """Test: Factory raises ValueError for unsupported modes"""
        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported validation mode"):
            factory.create('invalid_mode')
        
        with pytest.raises(ValueError, match="Unsupported validation mode"):
            factory.create('')
        
        with pytest.raises(ValueError, match="Unsupported validation mode"):
            factory.create('partial')  # Not implemented yet
    
    def test_get_available_modes(self, factory):
        """Test: Factory returns correct available modes"""
        # Act
        modes = factory.get_available_modes()
        
        # Assert
        assert 'comprehensive' in modes
        assert 'selective' in modes
        assert len(modes) == 2
    
    def test_is_mode_supported(self, factory):
        """Test: Factory correctly identifies supported modes"""
        # Act & Assert
        assert factory.is_mode_supported('comprehensive') is True
        assert factory.is_mode_supported('selective') is True
        assert factory.is_mode_supported('COMPREHENSIVE') is True
        assert factory.is_mode_supported('invalid') is False
        assert factory.is_mode_supported('') is False
    
    def test_get_strategy_info(self, factory):
        """Test: Factory provides strategy information"""
        # Act
        comp_info = factory.get_strategy_info('comprehensive')
        sel_info = factory.get_strategy_info('selective')
        
        # Assert comprehensive info
        assert comp_info['mode'] == 'comprehensive'
        assert comp_info['strategy_name'] == 'Comprehensive'
        assert comp_info['workflow_name'] == 'Kolegium'
        assert comp_info['expected_rule_range'] == (8, 12)
        assert comp_info['class_name'] == 'ComprehensiveStrategy'
        
        # Assert selective info
        assert sel_info['mode'] == 'selective'
        assert sel_info['strategy_name'] == 'Selective'
        assert sel_info['workflow_name'] == 'AI Writing Flow'
        assert sel_info['expected_rule_range'] == (3, 4)
        assert sel_info['class_name'] == 'SelectiveStrategy'
    
    def test_get_strategy_info_invalid_mode(self, factory):
        """Test: Strategy info raises error for invalid mode"""
        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported validation mode"):
            factory.get_strategy_info('invalid')
    
    
    def test_strategies_receive_repository_dependency(self, mock_repository):
        """Test: Created strategies receive repository dependency"""
        # Arrange
        factory = ValidationStrategyFactory(mock_repository)
        
        # Act
        comprehensive = factory.create('comprehensive')
        selective = factory.create('selective')
        
        # Assert - Strategies should have access to repository
        assert comprehensive.rule_repository is mock_repository
        assert selective.rule_repository is mock_repository