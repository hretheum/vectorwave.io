"""
Integration Tests: Dual Workflow Integration
Tests the complete dual workflow architecture with real strategy interactions.
"""
import pytest
from datetime import datetime

from src.application.services.validation_strategy_factory import ValidationStrategyFactory
from src.infrastructure.repositories.mock_rule_repository import MockRuleRepository
from src.domain.entities import ValidationRequest, ValidationMode, CheckpointType


class TestDualWorkflowIntegration:
    """Integration tests for dual workflow architecture"""
    
    @pytest.fixture
    def repository(self):
        """Mock repository with realistic data"""
        return MockRuleRepository()
    
    @pytest.fixture  
    def factory(self, repository):
        """ValidationStrategyFactory with mock repository"""
        return ValidationStrategyFactory(repository)
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for validation testing"""
        return """
        # Building Scalable Microservices with Docker and Kubernetes
        
        In this technical deep dive, we'll explore revolutionary approaches
        to building game-changing microservice architectures that leverage
        cutting-edge container orchestration.
        
        Our research shows significant improvements in system performance
        when implementing these patterns. The results are truly amazing
        and will transform your development workflow.
        
        ## Architecture Overview
        
        The system consists of multiple microservices that communicate
        through RESTful APIs. Each service is containerized using Docker
        and deployed on a Kubernetes cluster.
        
        ## Implementation Details
        
        We used Node.js for the backend services and React for the frontend.
        The database layer consists of PostgreSQL for transactional data
        and Redis for caching.
        
        ## Performance Results
        
        Our benchmarks show substantial performance gains across all metrics.
        The new architecture delivered amazing results that exceeded all
        expectations.
        """
    
    @pytest.mark.asyncio
    async def test_same_content_different_validation_depths(
        self,
        factory,
        sample_content
    ):
        """Test: Same input content processed by both strategies with different depths"""
        # Arrange
        comprehensive_request = ValidationRequest(
            content=sample_content,
            mode=ValidationMode.COMPREHENSIVE
        )
        
        selective_request = ValidationRequest(
            content=sample_content,
            mode=ValidationMode.SELECTIVE,
            checkpoint=CheckpointType.POST_WRITING
        )
        
        # Act
        comprehensive_strategy = factory.create('comprehensive')
        selective_strategy = factory.create('selective')
        
        comprehensive_rules = await comprehensive_strategy.validate(comprehensive_request)
        selective_rules = await selective_strategy.validate(selective_request)
        
        # Assert different rule counts
        assert 8 <= len(comprehensive_rules) <= 12  # Kolegium: comprehensive
        assert 3 <= len(selective_rules) <= 4       # AI Writing Flow: selective
        assert len(comprehensive_rules) > len(selective_rules)
        
        # Assert all rules have ChromaDB origin
        all_rules = comprehensive_rules + selective_rules
        for rule in all_rules:
            assert rule.chromadb_origin_metadata is not None
            assert 'collection_name' in rule.chromadb_origin_metadata
            assert 'timestamp' in rule.chromadb_origin_metadata
    
    @pytest.mark.asyncio
    async def test_comprehensive_validation_covers_all_aspects(
        self,
        factory,
        sample_content
    ):
        """Test: Comprehensive validation returns diverse rule types"""
        # Arrange
        request = ValidationRequest(
            content=sample_content,
            mode=ValidationMode.COMPREHENSIVE
        )
        
        # Act
        strategy = factory.create('comprehensive')
        rules = await strategy.validate(request)
        
        # Assert comprehensive coverage
        assert len(rules) >= 8
        
        # Check for diverse rule types
        rule_types = {rule.rule_type for rule in rules}
        assert len(rule_types) >= 3  # Should cover multiple types
        
        # Check for diverse severity levels
        severities = {rule.severity for rule in rules}
        assert len(severities) >= 2  # Should have different severities
        
        # Verify all rules are from ChromaDB
        collections = {rule.get_origin_collection() for rule in rules}
        assert len(collections) >= 1  # At least one collection
    
    @pytest.mark.asyncio
    async def test_selective_validation_checkpoint_specific(
        self,
        factory,
        sample_content
    ):
        """Test: Selective validation returns checkpoint-appropriate rules"""
        checkpoints = [
            CheckpointType.PRE_WRITING,
            CheckpointType.MID_WRITING, 
            CheckpointType.POST_WRITING
        ]
        
        strategy = factory.create('selective')
        
        for checkpoint in checkpoints:
            # Arrange
            request = ValidationRequest(
                content=sample_content,
                mode=ValidationMode.SELECTIVE,
                checkpoint=checkpoint
            )
            
            # Act
            rules = await strategy.validate(request)
            
            # Assert checkpoint-specific rules
            assert 3 <= len(rules) <= 4
            
            # Verify rules are relevant to checkpoint
            for rule in rules:
                # Check metadata contains checkpoint info (in mock implementation)
                metadata = rule.chromadb_origin_metadata
                if 'checkpoint' in metadata:
                    assert metadata['checkpoint'] == checkpoint.value
    
    @pytest.mark.asyncio
    async def test_workflow_separation_clean(
        self,
        factory,
        sample_content
    ):
        """Test: Clean separation between workflow types"""
        # Arrange
        comprehensive_request = ValidationRequest(
            content=sample_content,
            mode=ValidationMode.COMPREHENSIVE
        )
        
        selective_request = ValidationRequest(
            content=sample_content,
            mode=ValidationMode.SELECTIVE,
            checkpoint=CheckpointType.MID_WRITING
        )
        
        # Act
        comp_strategy = factory.create('comprehensive')
        sel_strategy = factory.create('selective')
        
        # Assert strategy separation
        assert comp_strategy.supports_request(comprehensive_request) is True
        assert comp_strategy.supports_request(selective_request) is False
        
        assert sel_strategy.supports_request(selective_request) is True
        assert sel_strategy.supports_request(comprehensive_request) is False
        
        # Assert workflow names
        assert comp_strategy.get_workflow_name() == "Kolegium"
        assert sel_strategy.get_workflow_name() == "AI Writing Flow"
    
    @pytest.mark.asyncio
    async def test_factory_creates_correct_strategies_for_modes(self, factory):
        """Test: Factory creates appropriate strategies for each mode"""
        # Act
        comprehensive = factory.create('comprehensive')
        selective = factory.create('selective')
        
        # Assert strategy types
        assert comprehensive.get_strategy_name() == "Comprehensive"
        assert comprehensive.get_workflow_name() == "Kolegium"
        assert comprehensive.get_expected_rule_count_range() == (8, 12)
        
        assert selective.get_strategy_name() == "Selective"
        assert selective.get_workflow_name() == "AI Writing Flow"
        assert selective.get_expected_rule_count_range() == (3, 4)
    
    @pytest.mark.asyncio
    async def test_no_hardcoded_rules_in_entire_system(
        self,
        factory,
        sample_content
    ):
        """Test: Entire system contains no hardcoded rules"""
        # Test comprehensive workflow
        comp_request = ValidationRequest(
            content=sample_content,
            mode=ValidationMode.COMPREHENSIVE
        )
        comp_strategy = factory.create('comprehensive')
        comp_rules = await comp_strategy.validate(comp_request)
        
        # Test selective workflow for all checkpoints
        sel_strategy = factory.create('selective')
        all_selective_rules = []
        
        for checkpoint in CheckpointType:
            sel_request = ValidationRequest(
                content=sample_content,
                mode=ValidationMode.SELECTIVE,
                checkpoint=checkpoint
            )
            sel_rules = await sel_strategy.validate(sel_request)
            all_selective_rules.extend(sel_rules)
        
        # Assert NO hardcoded rules anywhere
        all_rules = comp_rules + all_selective_rules
        
        for rule in all_rules:
            # Every rule MUST have ChromaDB origin metadata
            assert rule.chromadb_origin_metadata is not None
            assert len(rule.chromadb_origin_metadata) > 0
            
            # Required metadata fields
            required_fields = {'collection_name', 'document_id', 'timestamp'}
            assert all(field in rule.chromadb_origin_metadata for field in required_fields)
            
            # Collection source must be specified
            assert rule.collection_source is not None
            assert len(rule.collection_source.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_performance_both_strategies_under_200ms(
        self,
        factory,
        sample_content
    ):
        """Test: Both strategies perform validation under 200ms"""
        import time
        
        # Test comprehensive strategy performance
        comp_request = ValidationRequest(
            content=sample_content,
            mode=ValidationMode.COMPREHENSIVE
        )
        comp_strategy = factory.create('comprehensive')
        
        start_time = time.time()
        await comp_strategy.validate(comp_request)
        comp_duration = (time.time() - start_time) * 1000  # Convert to ms
        
        # Test selective strategy performance
        sel_request = ValidationRequest(
            content=sample_content,
            mode=ValidationMode.SELECTIVE,
            checkpoint=CheckpointType.POST_WRITING
        )
        sel_strategy = factory.create('selective')
        
        start_time = time.time()
        await sel_strategy.validate(sel_request)
        sel_duration = (time.time() - start_time) * 1000  # Convert to ms
        
        # Assert performance targets
        # Note: Mock repository is very fast, real ChromaDB will be slower
        # This test ensures the architecture doesn't add significant overhead
        assert comp_duration < 200, f"Comprehensive validation took {comp_duration:.2f}ms"
        assert sel_duration < 200, f"Selective validation took {sel_duration:.2f}ms"
        
        # Selective should generally be faster (fewer rules)
        # But this may not always be true with real ChromaDB queries
        print(f"Comprehensive: {comp_duration:.2f}ms, Selective: {sel_duration:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_repository_integration_health_check(self, repository):
        """Test: Repository integration is healthy"""
        # Act
        is_healthy = await repository.health_check()
        stats = await repository.get_collection_stats()
        
        # Assert
        assert is_healthy is True
        assert 'collections' in stats
        assert 'total_rules' in stats
        assert stats['total_rules'] > 0