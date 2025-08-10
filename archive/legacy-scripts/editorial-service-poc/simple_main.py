"""
Editorial Service - Simplified version for testing
Dual Workflow Support without ChromaDB dependency
"""

import os
import time
from typing import Dict, List, Optional, Literal
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

# Configure structured logging
logger = structlog.get_logger()

app = FastAPI(
    title="Editorial Service",
    description="Shared service for AI Writing Flow and Kolegium dual workflow validation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Types
ValidationMode = Literal["comprehensive", "selective"]
CheckpointType = Literal["pre-writing", "mid-writing", "post-writing"]

class ValidationRequest(BaseModel):
    content: str = Field(..., description="Content to validate")
    mode: ValidationMode = Field(..., description="Validation mode: comprehensive or selective")
    checkpoint: Optional[CheckpointType] = Field(None, description="Checkpoint for selective validation")

class ValidationRule(BaseModel):
    rule_id: str
    rule_name: str
    rule_type: str
    description: str
    severity: str
    collection_source: str
    chromadb_origin_metadata: Dict

class ValidationResponse(BaseModel):
    mode: ValidationMode
    checkpoint: Optional[CheckpointType]
    rules_applied: List[ValidationRule]
    rule_count: int
    processing_time_ms: float
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    chromadb_connected: bool
    cache_status: str
    dual_workflow_ready: bool

def get_selective_rules_for_checkpoint(checkpoint: CheckpointType) -> List[ValidationRule]:
    """Return selective validation rules for specific checkpoints"""
    checkpoint_rules = {
        "pre-writing": [
            ValidationRule(
                rule_id="pub_type_001",
                rule_name="publication_type_match",
                rule_type="structural",
                description="Content matches selected publication type requirements",
                severity="high",
                collection_source="publication_platform_rules",
                chromadb_origin_metadata={"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
            ),
            ValidationRule(
                rule_id="aud_tgt_001", 
                rule_name="audience_targeting",
                rule_type="content",
                description="Content targets appropriate audience segment",
                severity="high",
                collection_source="publication_platform_rules",
                chromadb_origin_metadata={"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
            ),
            ValidationRule(
                rule_id="str_bas_001",
                rule_name="structure_basic",
                rule_type="structural", 
                description="Basic content structure requirements met",
                severity="medium",
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            )
        ],
        "mid-writing": [
            ValidationRule(
                rule_id="sty_con_001",
                rule_name="style_consistency",
                rule_type="style",
                description="Writing style consistent with brand guidelines",
                severity="high",
                collection_source="style_editorial_rules", 
                chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            ),
            ValidationRule(
                rule_id="ton_mat_001",
                rule_name="tone_match",
                rule_type="style",
                description="Tone matches publication requirements",
                severity="high", 
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            ),
            ValidationRule(
                rule_id="flw_qua_001",
                rule_name="flow_quality",
                rule_type="content",
                description="Content flow and readability standards met",
                severity="medium",
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            )
        ],
        "post-writing": [
            ValidationRule(
                rule_id="hum_chk_001",
                rule_name="humanization_check", 
                rule_type="quality",
                description="Content passes AI detection avoidance checks",
                severity="high",
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            ),
            ValidationRule(
                rule_id="aid_avo_001",
                rule_name="ai_detection_avoid",
                rule_type="quality",
                description="Anti-AI detection patterns implemented", 
                severity="high",
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            ),
            ValidationRule(
                rule_id="fin_pol_001", 
                rule_name="final_polish",
                rule_type="quality",
                description="Final editorial polish and quality gates passed",
                severity="medium",
                collection_source="style_editorial_rules",
                chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            )
        ]
    }
    
    return checkpoint_rules.get(checkpoint, [])

def get_comprehensive_rules() -> List[ValidationRule]:
    """Return comprehensive validation rules covering all aspects"""
    return [
        # Style rules from style_editorial_rules collection
        ValidationRule(
            rule_id="sty_con_001", rule_name="style_consistency", rule_type="style",
            description="Writing style consistent with brand guidelines", severity="high",
            collection_source="style_editorial_rules",
            chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
        ),
        ValidationRule(
            rule_id="ton_mat_001", rule_name="tone_match", rule_type="style", 
            description="Tone matches publication requirements", severity="high",
            collection_source="style_editorial_rules",
            chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
        ),
        ValidationRule(
            rule_id="str_req_001", rule_name="structure_requirements", rule_type="structural",
            description="Content structure meets publication standards", severity="high",
            collection_source="style_editorial_rules", 
            chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
        ),
        # Platform rules from publication_platform_rules collection
        ValidationRule(
            rule_id="plt_opt_001", rule_name="platform_optimization", rule_type="platform",
            description="Content optimized for target platforms", severity="medium",
            collection_source="publication_platform_rules",
            chromadb_origin_metadata={"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
        ),
        ValidationRule(
            rule_id="aud_tgt_001", rule_name="audience_targeting", rule_type="content",
            description="Content targets appropriate audience segment", severity="high", 
            collection_source="publication_platform_rules",
            chromadb_origin_metadata={"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
        ),
        # Quality rules
        ValidationRule(
            rule_id="qua_gat_001", rule_name="quality_gates", rule_type="quality",
            description="All quality gates and standards met", severity="high",
            collection_source="style_editorial_rules",
            chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
        ),
        ValidationRule(
            rule_id="hum_chk_001", rule_name="humanization_check", rule_type="quality", 
            description="Content passes AI detection avoidance checks", severity="high",
            collection_source="style_editorial_rules",
            chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
        ),
        # Additional comprehensive rules
        ValidationRule(
            rule_id="seo_opt_001", rule_name="seo_optimization", rule_type="platform",
            description="SEO best practices implemented", severity="medium",
            collection_source="publication_platform_rules", 
            chromadb_origin_metadata={"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
        ),
        ValidationRule(
            rule_id="eng_met_001", rule_name="engagement_metrics", rule_type="content",
            description="Content structured for high engagement", severity="medium",
            collection_source="publication_platform_rules",
            chromadb_origin_metadata={"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
        ),
        ValidationRule(
            rule_id="bra_ali_001", rule_name="brand_alignment", rule_type="style",
            description="Content aligns with brand voice and values", severity="high", 
            collection_source="style_editorial_rules",
            chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
        ),
        ValidationRule(
            rule_id="com_pli_001", rule_name="compliance_check", rule_type="quality",
            description="Content meets compliance and legal requirements", severity="high",
            collection_source="style_editorial_rules",
            chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
        )
    ]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with dual workflow status"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        chromadb_connected=True,  # Simulated for testing
        cache_status="ready",
        dual_workflow_ready=True
    )

@app.post("/validate/comprehensive", response_model=ValidationResponse)
async def validate_comprehensive(request: ValidationRequest):
    """
    Comprehensive validation for Kolegium workflow.
    Returns 8-12 rules covering all aspects: style, structure, platform, audience.
    """
    start_time = time.time()
    
    # Get comprehensive rules (8-12 rules)
    rules = get_comprehensive_rules()
    
    processing_time = (time.time() - start_time) * 1000
    
    logger.info(
        "Comprehensive validation completed",
        rule_count=len(rules),
        processing_time_ms=processing_time,
        mode="comprehensive"
    )
    
    return ValidationResponse(
        mode="comprehensive",
        checkpoint=None,
        rules_applied=rules,
        rule_count=len(rules),
        processing_time_ms=processing_time,
        timestamp=datetime.utcnow()
    )

@app.post("/validate/selective", response_model=ValidationResponse) 
async def validate_selective(request: ValidationRequest):
    """
    Selective validation for AI Writing Flow workflow.
    Returns 3-4 focused rules based on checkpoint.
    """
    start_time = time.time()
    
    if not request.checkpoint:
        raise HTTPException(
            status_code=400, 
            detail="Checkpoint required for selective validation. Use: pre-writing, mid-writing, or post-writing"
        )
    
    # Get selective rules for specific checkpoint (3 rules each)
    rules = get_selective_rules_for_checkpoint(request.checkpoint)
    
    processing_time = (time.time() - start_time) * 1000
    
    logger.info(
        "Selective validation completed",
        checkpoint=request.checkpoint,
        rule_count=len(rules),
        processing_time_ms=processing_time,
        mode="selective"
    )
    
    return ValidationResponse(
        mode="selective", 
        checkpoint=request.checkpoint,
        rules_applied=rules,
        rule_count=len(rules),
        processing_time_ms=processing_time,
        timestamp=datetime.utcnow()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8040)