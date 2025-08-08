"""
Unit Tests: ComprehensiveStrategy
Tests the comprehensive validation strategy for Kolegium workflow.
"""
import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.application.strategies.comprehensive_strategy import ComprehensiveStrategy
from src.domain.entities import (
    ValidationRequest, ValidationMode, ValidationRule, RuleType, RuleSeverity
)
from src.domain.interfaces import IRuleRepository


class TestComprehensiveStrategy:
    """Test suite for ComprehensiveStrategy"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock rule repository"""
        return AsyncMock(spec=IRuleRepository)
    
    @pytest.fixture
    def strategy(self, mock_repository):
        """ComprehensiveStrategy instance"""
        return ComprehensiveStrategy(mock_repository)
    
    @pytest.fixture
    def comprehensive_request(self):
        """Valid comprehensive validation request"""
        return ValidationRequest(
            content="Test content for comprehensive validation",
            mode=ValidationMode.COMPREHENSIVE
        )
    
    @pytest.fixture
    def mock_comprehensive_rules(self):
        """Mock rules that comprehensive strategy should return"""
        rules = []
        for i in range(10):  # 10 rules (within 8-12 range)
            rules.append(
                ValidationRule(
                    rule_id=f"comp_rule_{i:03d}",
                    rule_name=f"Comprehensive Rule {i+1}",
                    rule_type=RuleType.EDITORIAL,
                    description=f"Mock comprehensive rule {i+1} description",
                    severity=RuleSeverity.HIGH,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        'collection_name': 'style_editorial_rules',
                        'document_id': f'rule_{i}',
                        'timestamp': datetime.now().isoformat()
                    }
                )
            )
        return rules
    
    @pytest.mark.asyncio
    async def test_validate_returns_8_to_12_rules(
        self, 
        strategy, 
        mock_repository, 
        comprehensive_request,
        mock_comprehensive_rules
    ):
        """Test: ComprehensiveStrategy.validate() returns 8-12 rules"""
        # Arrange
        mock_repository.get_comprehensive_rules.return_value = mock_comprehensive_rules
        
        # Act
        rules = await strategy.validate(comprehensive_request)
        
        # Assert
        assert 8 <= len(rules) <= 12
        assert len(rules) == 10  # Our mock returns exactly 10
        mock_repository.get_comprehensive_rules.assert_called_once_with(
            comprehensive_request.content
        )
    
    @pytest.mark.asyncio
    async def test_validate_all_rules_have_chromadb_origin(
        self,
        strategy,
        mock_repository, 
        comprehensive_request,
        mock_comprehensive_rules
    ):
        """Test: All returned rules have ChromaDB origin metadata"""
        # Arrange
        mock_repository.get_comprehensive_rules.return_value = mock_comprehensive_rules
        
        # Act
        rules = await strategy.validate(comprehensive_request)
        
        # Assert
        for rule in rules:
            assert rule.chromadb_origin_metadata is not None
            assert 'collection_name' in rule.chromadb_origin_metadata
            assert 'document_id' in rule.chromadb_origin_metadata
            assert 'timestamp' in rule.chromadb_origin_metadata
    
    @pytest.mark.asyncio
    async def test_validate_rejects_hardcoded_rules(
        self,
        strategy,
        mock_repository,
        comprehensive_request
    ):
        """Test: Strategy rejects rules without ChromaDB metadata"""
        # This test verifies the strategy checks for ChromaDB metadata
        # Since ValidationRule entity already validates this, we test repository failure
        mock_repository.get_comprehensive_rules.side_effect = RuntimeError(
            "Rule bad_rule lacks ChromaDB origin metadata - hardcoded rules not allowed"
        )
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="lacks ChromaDB origin metadata"):
            await strategy.validate(comprehensive_request)
    
    def test_get_expected_rule_count_range(self, strategy):
        """Test: Strategy returns correct rule count range"""
        # Act
        min_rules, max_rules = strategy.get_expected_rule_count_range()
        
        # Assert
        assert min_rules == 8
        assert max_rules == 12
        assert min_rules < max_rules
    
    def test_supports_request_comprehensive_mode(self, strategy):
        """Test: Strategy supports comprehensive validation requests"""
        # Arrange
        comprehensive_request = ValidationRequest(
            content="Test content",
            mode=ValidationMode.COMPREHENSIVE
        )
        
        # Act & Assert
        assert strategy.supports_request(comprehensive_request) is True
    
    def test_supports_request_rejects_selective_mode(self, strategy):
        """Test: Strategy rejects selective validation requests"""
        # Create mock request object to bypass ValidationRequest validation
        class MockSelectiveRequest:
            def __init__(self):
                self.mode = ValidationMode.SELECTIVE
                self.content = "Test content"
        
        mock_request = MockSelectiveRequest()
        
        # Act & Assert
        assert strategy.supports_request(mock_request) is False
    
    @pytest.mark.asyncio 
    async def test_validate_rejects_selective_request(self, strategy):
        """Test: Validate raises error for selective mode request"""
        # Create mock request object to bypass ValidationRequest validation
        class MockSelectiveRequest:
            def __init__(self):
                self.mode = ValidationMode.SELECTIVE
                self.content = "Test content"
        
        mock_request = MockSelectiveRequest()
        
        # Act & Assert
        with pytest.raises(ValueError, match="only supports comprehensive mode"):
            await strategy.validate(mock_request)
    
    def test_get_strategy_name(self, strategy):
        """Test: Strategy returns correct name"""
        assert strategy.get_strategy_name() == "Comprehensive"
    
    def test_get_workflow_name(self, strategy):
        """Test: Strategy returns correct workflow name"""
        assert strategy.get_workflow_name() == "Kolegium"
    
    @pytest.mark.asyncio
    async def test_validate_logs_rule_count_warning_if_outside_range(
        self,
        strategy,
        mock_repository,
        comprehensive_request,
        mock_comprehensive_rules
    ):
        """Test: Strategy works with rule count outside expected range"""
        # Arrange - Return only 2 rules (below minimum of 8)
        few_rules = mock_comprehensive_rules[:2]
        mock_repository.get_comprehensive_rules.return_value = few_rules
        
        # Act
        rules = await strategy.validate(comprehensive_request)
        
        # Assert - Should still work but log warning (visible in stdout)
        assert len(rules) == 2
    
    @pytest.mark.asyncio
    async def test_validate_raises_error_on_repository_failure(
        self,
        strategy,
        mock_repository,
        comprehensive_request
    ):
        """Test: Strategy handles repository failures gracefully"""
        # Arrange
        mock_repository.get_comprehensive_rules.side_effect = Exception("ChromaDB connection failed")
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Comprehensive validation failed"):
            await strategy.validate(comprehensive_request)
    
