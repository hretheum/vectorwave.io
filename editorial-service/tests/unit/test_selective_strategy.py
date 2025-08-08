"""
Unit Tests: SelectiveStrategy
Tests the selective validation strategy for AI Writing Flow workflow.
"""
import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.application.strategies.selective_strategy import SelectiveStrategy
from src.domain.entities import (
    ValidationRequest, ValidationMode, CheckpointType,
    ValidationRule, RuleType, RuleSeverity
)
from src.domain.interfaces import IRuleRepository


class TestSelectiveStrategy:
    """Test suite for SelectiveStrategy"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock rule repository"""
        return AsyncMock(spec=IRuleRepository)
    
    @pytest.fixture
    def strategy(self, mock_repository):
        """SelectiveStrategy instance"""
        return SelectiveStrategy(mock_repository)
    
    @pytest.fixture
    def selective_request(self):
        """Valid selective validation request"""
        return ValidationRequest(
            content="Test content for selective validation",
            mode=ValidationMode.SELECTIVE,
            checkpoint=CheckpointType.PRE_WRITING
        )
    
    @pytest.fixture
    def mock_selective_rules(self):
        """Mock rules that selective strategy should return"""
        rules = []
        for i in range(4):  # 4 rules (within 3-4 range)
            rules.append(
                ValidationRule(
                    rule_id=f"sel_rule_{i:03d}",
                    rule_name=f"Selective Rule {i+1}",
                    rule_type=RuleType.CONTENT,
                    description=f"Mock selective rule {i+1} description",
                    severity=RuleSeverity.HIGH,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        'collection_name': 'style_editorial_rules',
                        'document_id': f'selective_rule_{i}',
                        'timestamp': datetime.now().isoformat(),
                        'checkpoint': 'pre-writing'
                    }
                )
            )
        return rules
    
    @pytest.mark.asyncio
    async def test_validate_returns_3_to_4_rules(
        self,
        strategy,
        mock_repository,
        selective_request,
        mock_selective_rules
    ):
        """Test: SelectiveStrategy.validate() returns 3-4 rules"""
        # Arrange
        mock_repository.get_selective_rules.return_value = mock_selective_rules
        
        # Act
        rules = await strategy.validate(selective_request)
        
        # Assert
        assert 3 <= len(rules) <= 4
        assert len(rules) == 4  # Our mock returns exactly 4
        mock_repository.get_selective_rules.assert_called_once_with(
            selective_request.content,
            selective_request.checkpoint
        )
    
    @pytest.mark.asyncio
    async def test_validate_all_rules_have_chromadb_origin(
        self,
        strategy,
        mock_repository,
        selective_request, 
        mock_selective_rules
    ):
        """Test: All returned rules have ChromaDB origin metadata"""
        # Arrange
        mock_repository.get_selective_rules.return_value = mock_selective_rules
        
        # Act
        rules = await strategy.validate(selective_request)
        
        # Assert
        for rule in rules:
            assert rule.chromadb_origin_metadata is not None
            assert 'collection_name' in rule.chromadb_origin_metadata
            assert 'document_id' in rule.chromadb_origin_metadata
            assert 'timestamp' in rule.chromadb_origin_metadata
    
    @pytest.mark.asyncio
    async def test_validate_works_with_different_checkpoints(
        self,
        strategy,
        mock_repository,
        mock_selective_rules
    ):
        """Test: Strategy works with all checkpoint types"""
        # Test each checkpoint type
        checkpoints = [
            CheckpointType.PRE_WRITING,
            CheckpointType.MID_WRITING,
            CheckpointType.POST_WRITING
        ]
        
        for checkpoint in checkpoints:
            # Arrange
            request = ValidationRequest(
                content="Test content",
                mode=ValidationMode.SELECTIVE,
                checkpoint=checkpoint
            )
            mock_repository.get_selective_rules.return_value = mock_selective_rules
            
            # Act
            rules = await strategy.validate(request)
            
            # Assert
            assert 3 <= len(rules) <= 4
            mock_repository.get_selective_rules.assert_called_with(
                request.content,
                checkpoint
            )
    
    @pytest.mark.asyncio
    async def test_validate_rejects_hardcoded_rules(
        self,
        strategy,
        mock_repository,
        selective_request
    ):
        """Test: Strategy rejects rules without ChromaDB metadata"""
        # Test repository failure due to hardcoded rules
        mock_repository.get_selective_rules.side_effect = RuntimeError(
            "Rule bad_rule lacks ChromaDB origin metadata - hardcoded rules not allowed"
        )
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="lacks ChromaDB origin metadata"):
            await strategy.validate(selective_request)
    
    def test_get_expected_rule_count_range(self, strategy):
        """Test: Strategy returns correct rule count range"""
        # Act
        min_rules, max_rules = strategy.get_expected_rule_count_range()
        
        # Assert
        assert min_rules == 3
        assert max_rules == 4
        assert min_rules < max_rules
    
    def test_supports_request_selective_mode_with_checkpoint(self, strategy):
        """Test: Strategy supports selective validation requests with checkpoint"""
        # Arrange
        selective_request = ValidationRequest(
            content="Test content",
            mode=ValidationMode.SELECTIVE,
            checkpoint=CheckpointType.MID_WRITING
        )
        
        # Act & Assert
        assert strategy.supports_request(selective_request) is True
    
    def test_supports_request_rejects_comprehensive_mode(self, strategy):
        """Test: Strategy rejects comprehensive validation requests"""
        # Arrange
        comprehensive_request = ValidationRequest(
            content="Test content",
            mode=ValidationMode.COMPREHENSIVE
        )
        
        # Act & Assert
        assert strategy.supports_request(comprehensive_request) is False
    
    def test_supports_request_rejects_selective_without_checkpoint(self, strategy):
        """Test: Strategy rejects selective requests without checkpoint"""
        # Note: ValidationRequest itself validates this, but strategy should also check
        # This test verifies defensive programming
        
        # Create a mock request that bypasses ValidationRequest validation
        class MockRequest:
            def __init__(self):
                self.mode = ValidationMode.SELECTIVE
                self.checkpoint = None
                self.content = "Test content"
        
        mock_request = MockRequest()
        
        # Act & Assert
        assert strategy.supports_request(mock_request) is False
    
    @pytest.mark.asyncio
    async def test_validate_rejects_comprehensive_request(self, strategy):
        """Test: Validate raises error for comprehensive mode request"""
        # Arrange
        comprehensive_request = ValidationRequest(
            content="Test content",
            mode=ValidationMode.COMPREHENSIVE
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="only supports selective mode"):
            await strategy.validate(comprehensive_request)
    
    def test_get_strategy_name(self, strategy):
        """Test: Strategy returns correct name"""
        assert strategy.get_strategy_name() == "Selective"
    
    def test_get_workflow_name(self, strategy):
        """Test: Strategy returns correct workflow name"""
        assert strategy.get_workflow_name() == "AI Writing Flow"
    
    
    @pytest.mark.asyncio
    async def test_validate_raises_error_on_repository_failure(
        self,
        strategy,
        mock_repository,
        selective_request
    ):
        """Test: Strategy handles repository failures gracefully"""
        # Arrange
        mock_repository.get_selective_rules.side_effect = Exception("ChromaDB connection failed")
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Selective validation failed"):
            await strategy.validate(selective_request)
    
