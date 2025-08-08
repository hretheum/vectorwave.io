"""
Infrastructure Repository: MockRuleRepository
Mock implementation for testing and development purposes.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from ...domain.entities import (
    ValidationRule, RuleType, RuleSeverity, CheckpointType
)
from ...domain.interfaces import IRuleRepository

logger = structlog.get_logger()


class MockRuleRepository(IRuleRepository):
    """
    Mock repository implementation for testing validation strategies.
    
    Provides predefined rule sets that simulate ChromaDB responses
    while maintaining the contract that all rules must have ChromaDB origin metadata.
    
    This is ONLY for testing - production must use real ChromaDB repository.
    """
    
    def __init__(self):
        """Initialize mock repository with predefined rules"""
        self._comprehensive_rules = self._create_comprehensive_rules()
        self._selective_rules = self._create_selective_rules()
        
        logger.info(
            "MockRuleRepository initialized",
            comprehensive_rules=len(self._comprehensive_rules),
            selective_rules=len(self._selective_rules),
            note="THIS IS A MOCK - Production must use ChromaDB"
        )
    
    def _create_comprehensive_rules(self) -> List[ValidationRule]:
        """Create comprehensive rule set (8-12 rules for Kolegium)"""
        base_metadata = {
            'collection_name': 'style_editorial_rules',
            'document_id': 'comprehensive_set',
            'timestamp': datetime.now().isoformat(),
            'mock_warning': 'This is mock data - production must use ChromaDB'
        }
        
        return [
            ValidationRule(
                rule_id="comp_001",
                rule_name="Evidence-Based Writing",
                rule_type=RuleType.EDITORIAL,
                description="Minimum 3 primary sources, data <6 months old",
                severity=RuleSeverity.CRITICAL,
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={**base_metadata, 'rule_category': 'evidence'}
            ),
            ValidationRule(
                rule_id="comp_002", 
                rule_name="Anti-Buzzword Policy",
                rule_type=RuleType.STYLE,
                description="Forbidden: 'revolutionary', 'game-changing', 'leverage'",
                severity=RuleSeverity.HIGH,
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={**base_metadata, 'rule_category': 'language'}
            ),
            ValidationRule(
                rule_id="comp_003",
                rule_name="Specific Metrics Required",
                rule_type=RuleType.CONTENT,
                description="Use concrete numbers instead of 'significant' or 'substantial'",
                severity=RuleSeverity.HIGH,
                collection_source="style_editorial_rules", 
                chromadb_origin_metadata={**base_metadata, 'rule_category': 'precision'}
            ),
            ValidationRule(
                rule_id="comp_004",
                rule_name="Audience Targeting",
                rule_type=RuleType.CONTENT,
                description="Address Technical Founder (35%), Senior Engineer (30%), Decision Maker (25%)",
                severity=RuleSeverity.MEDIUM,
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={**base_metadata, 'rule_category': 'audience'}
            ),
            ValidationRule(
                rule_id="comp_005",
                rule_name="Source Transparency",
                rule_type=RuleType.EDITORIAL,
                description="'Show Our Work' - all sources must be visible and verifiable",
                severity=RuleSeverity.HIGH,
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={**base_metadata, 'rule_category': 'transparency'}
            ),
            ValidationRule(
                rule_id="comp_006",
                rule_name="Platform Optimization",
                rule_type=RuleType.PLATFORM,
                description="LinkedIn: First 2 lines hook, paragraphs max 2-3 sentences",
                severity=RuleSeverity.MEDIUM,
                collection_source="publication_platform_rules",
                chromadb_origin_metadata={**base_metadata, 'rule_category': 'platform'}
            ),
            ValidationRule(
                rule_id="comp_007",
                rule_name="Visual Hierarchy",
                rule_type=RuleType.STYLE,
                description="H2 headers max every 400 words, bullet points for scanability",
                severity=RuleSeverity.MEDIUM,
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={**base_metadata, 'rule_category': 'structure'}
            ),
            ValidationRule(
                rule_id="comp_008",
                rule_name="Technical Accuracy",
                rule_type=RuleType.TECHNICAL,
                description="Code examples must compile, dependencies <6 months old",
                severity=RuleSeverity.CRITICAL,
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={**base_metadata, 'rule_category': 'technical'}
            ),
            ValidationRule(
                rule_id="comp_009",
                rule_name="Engagement Hooks", 
                rule_type=RuleType.CONTENT,
                description="Contrarian statement in first sentence, specific CTA at end",
                severity=RuleSeverity.MEDIUM,
                collection_source="publication_platform_rules",
                chromadb_origin_metadata={**base_metadata, 'rule_category': 'engagement'}
            ),
            ValidationRule(
                rule_id="comp_010",
                rule_name="Human-AI Distinction",
                rule_type=RuleType.CONTENT,
                description="Personal experiences, 'I discovered', debugging war stories",
                severity=RuleSeverity.HIGH,
                collection_source="style_editorial_rules", 
                chromadb_origin_metadata={**base_metadata, 'rule_category': 'humanization'}
            )
        ]
    
    def _create_selective_rules(self) -> Dict[CheckpointType, List[ValidationRule]]:
        """Create selective rule sets per checkpoint (3-4 rules each)"""
        base_metadata = {
            'collection_name': 'style_editorial_rules',
            'timestamp': datetime.now().isoformat(),
            'mock_warning': 'This is mock data - production must use ChromaDB'
        }
        
        return {
            CheckpointType.PRE_WRITING: [
                ValidationRule(
                    rule_id="sel_pre_001",
                    rule_name="Audience Definition",
                    rule_type=RuleType.CONTENT,
                    description="Clearly identify target audience percentage breakdown",
                    severity=RuleSeverity.CRITICAL,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        **base_metadata, 
                        'document_id': 'pre_writing_checkpoint',
                        'checkpoint': 'pre-writing'
                    }
                ),
                ValidationRule(
                    rule_id="sel_pre_002",
                    rule_name="Evidence Planning",
                    rule_type=RuleType.EDITORIAL,
                    description="Plan minimum 3 primary sources before writing",
                    severity=RuleSeverity.HIGH,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        **base_metadata,
                        'document_id': 'pre_writing_checkpoint', 
                        'checkpoint': 'pre-writing'
                    }
                ),
                ValidationRule(
                    rule_id="sel_pre_003",
                    rule_name="Structure Outline",
                    rule_type=RuleType.STYLE,
                    description="Define clear H2 structure before content creation",
                    severity=RuleSeverity.MEDIUM,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        **base_metadata,
                        'document_id': 'pre_writing_checkpoint',
                        'checkpoint': 'pre-writing'
                    }
                )
            ],
            
            CheckpointType.MID_WRITING: [
                ValidationRule(
                    rule_id="sel_mid_001",
                    rule_name="Flow Coherence",
                    rule_type=RuleType.CONTENT,
                    description="Each paragraph connects logically to the next",
                    severity=RuleSeverity.HIGH,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        **base_metadata,
                        'document_id': 'mid_writing_checkpoint',
                        'checkpoint': 'mid-writing'
                    }
                ),
                ValidationRule(
                    rule_id="sel_mid_002",
                    rule_name="Buzzword Check",
                    rule_type=RuleType.STYLE,
                    description="Avoid 'revolutionary', 'game-changing', 'leverage'",
                    severity=RuleSeverity.MEDIUM,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        **base_metadata,
                        'document_id': 'mid_writing_checkpoint',
                        'checkpoint': 'mid-writing'
                    }
                ),
                ValidationRule(
                    rule_id="sel_mid_003",
                    rule_name="Specificity Check",
                    rule_type=RuleType.CONTENT,
                    description="Replace vague terms with concrete metrics",
                    severity=RuleSeverity.HIGH,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        **base_metadata,
                        'document_id': 'mid_writing_checkpoint',
                        'checkpoint': 'mid-writing'
                    }
                ),
                ValidationRule(
                    rule_id="sel_mid_004",
                    rule_name="Source Integration",
                    rule_type=RuleType.EDITORIAL,
                    description="Verify sources are properly cited and recent",
                    severity=RuleSeverity.CRITICAL,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        **base_metadata,
                        'document_id': 'mid_writing_checkpoint',
                        'checkpoint': 'mid-writing'
                    }
                )
            ],
            
            CheckpointType.POST_WRITING: [
                ValidationRule(
                    rule_id="sel_post_001",
                    rule_name="Platform Optimization",
                    rule_type=RuleType.PLATFORM,
                    description="Optimize for target platform (LinkedIn, Substack, etc.)",
                    severity=RuleSeverity.HIGH,
                    collection_source="publication_platform_rules",
                    chromadb_origin_metadata={
                        **base_metadata,
                        'document_id': 'post_writing_checkpoint',
                        'checkpoint': 'post-writing'
                    }
                ),
                ValidationRule(
                    rule_id="sel_post_002",
                    rule_name="CTA Clarity",
                    rule_type=RuleType.CONTENT,
                    description="Specific, actionable call-to-action at conclusion",
                    severity=RuleSeverity.MEDIUM,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        **base_metadata,
                        'document_id': 'post_writing_checkpoint',
                        'checkpoint': 'post-writing'
                    }
                ),
                ValidationRule(
                    rule_id="sel_post_003",
                    rule_name="Quality Gates",
                    rule_type=RuleType.EDITORIAL,
                    description="Final check: evidence, clarity, engagement elements",
                    severity=RuleSeverity.CRITICAL,
                    collection_source="style_editorial_rules",
                    chromadb_origin_metadata={
                        **base_metadata,
                        'document_id': 'post_writing_checkpoint',
                        'checkpoint': 'post-writing'
                    }
                )
            ]
        }
    
    async def get_comprehensive_rules(self, content: str) -> List[ValidationRule]:
        """Get comprehensive rule set (8-12 rules for Kolegium)"""
        logger.info(
            "Mock: Retrieving comprehensive rules", 
            content_length=len(content),
            rules_returned=len(self._comprehensive_rules)
        )
        return self._comprehensive_rules
    
    async def get_selective_rules(
        self, 
        content: str, 
        checkpoint: CheckpointType
    ) -> List[ValidationRule]:
        """Get selective rules for specific checkpoint (3-4 rules)"""
        rules = self._selective_rules.get(checkpoint, [])
        logger.info(
            "Mock: Retrieving selective rules",
            checkpoint=checkpoint.value,
            content_length=len(content), 
            rules_returned=len(rules)
        )
        return rules
    
    async def get_rules_by_type(
        self, 
        rule_type: RuleType,
        limit: Optional[int] = None
    ) -> List[ValidationRule]:
        """Get rules filtered by type"""
        all_rules = self._comprehensive_rules + [
            rule for rules in self._selective_rules.values() for rule in rules
        ]
        filtered = [rule for rule in all_rules if rule.rule_type == rule_type]
        
        if limit:
            filtered = filtered[:limit]
            
        return filtered
    
    async def get_rules_by_severity(
        self, 
        severity: RuleSeverity,
        limit: Optional[int] = None
    ) -> List[ValidationRule]:
        """Get rules filtered by severity"""
        all_rules = self._comprehensive_rules + [
            rule for rules in self._selective_rules.values() for rule in rules
        ]
        filtered = [rule for rule in all_rules if rule.severity == severity]
        
        if limit:
            filtered = filtered[:limit]
            
        return filtered
    
    async def search_rules(
        self, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ValidationRule]:
        """Search rules using mock semantic search"""
        # Simple mock search - match query against rule names/descriptions
        all_rules = self._comprehensive_rules + [
            rule for rules in self._selective_rules.values() for rule in rules
        ]
        
        query_lower = query.lower()
        matches = [
            rule for rule in all_rules
            if (query_lower in rule.rule_name.lower() or 
                query_lower in rule.description.lower())
        ]
        
        return matches[:limit]
    
    async def get_rule_by_id(self, rule_id: str) -> Optional[ValidationRule]:
        """Get specific rule by ID"""
        all_rules = self._comprehensive_rules + [
            rule for rules in self._selective_rules.values() for rule in rules
        ]
        
        for rule in all_rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get mock collection statistics"""
        return {
            'collections': {
                'style_editorial_rules': {
                    'count': len(self._comprehensive_rules) + sum(
                        len(rules) for rules in self._selective_rules.values()
                    ),
                    'status': 'healthy'
                },
                'publication_platform_rules': {
                    'count': 2,  # Mock platform rules in comprehensive set
                    'status': 'healthy'
                }
            },
            'total_rules': len(self._comprehensive_rules) + sum(
                len(rules) for rules in self._selective_rules.values()
            ),
            'mock_warning': 'This is mock data - production must use ChromaDB'
        }
    
    async def health_check(self) -> bool:
        """Mock health check - always returns True"""
        return True