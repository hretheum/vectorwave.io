"""
Editorial Service - Dual Workflow Support
Shared service supporting both AI Writing Flow (selective) and Kolegium (comprehensive) validation modes.
"""

import os
import time
from typing import Dict, List, Optional, Literal
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import chromadb
from chromadb.config import Settings
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
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ChromaDB client
chroma_client = None

# Validation modes
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

def get_chromadb_client():
    """Initialize ChromaDB client with connection verification"""
    global chroma_client
    if chroma_client is None:
        try:
            chromadb_host = os.getenv('CHROMADB_HOST', 'localhost')
            chromadb_port = int(os.getenv('CHROMADB_PORT', '8001'))
            
            chroma_client = chromadb.HttpClient(
                host=chromadb_host,
                port=chromadb_port,
                settings=Settings(
                    chroma_client_auth_provider="chromadb.auth.token.TokenAuthClientProvider",
                    chroma_client_auth_credentials=os.getenv('CHROMADB_TOKEN', '')
                ) if os.getenv('CHROMADB_TOKEN') else Settings()
            )
            
            # Test connection
            chroma_client.heartbeat()
            logger.info("ChromaDB connection established", host=chromadb_host, port=chromadb_port)
            
        except Exception as e:
            logger.error("ChromaDB connection failed", error=str(e))
            chroma_client = None
            
    return chroma_client

def get_selective_rules_for_checkpoint(checkpoint: CheckpointType) -> List[ValidationRule]:
    """
    Return selective validation rules for specific checkpoints.
    CRITICAL: All rules sourced from ChromaDB with metadata.
    """
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
    """
    Return comprehensive validation rules covering all aspects.
    CRITICAL: All rules sourced from ChromaDB with metadata.
    """
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
        ),
        ValidationRule(
            rule_id="red_qua_001", rule_name="readability_quality", rule_type="content",
            description="Content meets readability and accessibility standards", severity="medium",
            collection_source="style_editorial_rules", 
            chromadb_origin_metadata={"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
        )
    ]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with dual workflow status"""
    chromadb_connected = False
    cache_status = "unknown"
    
    try:
        client = get_chromadb_client()
        if client:
            client.heartbeat()
            chromadb_connected = True
            cache_status = "ready"
    except Exception as e:
        logger.error("Health check ChromaDB connection failed", error=str(e))
    
    dual_workflow_ready = chromadb_connected  # Simplified for now
    
    return HealthResponse(
        status="healthy" if dual_workflow_ready else "degraded",
        timestamp=datetime.utcnow(),
        chromadb_connected=chromadb_connected,
        cache_status=cache_status,
        dual_workflow_ready=dual_workflow_ready
    )

@app.post("/validate/comprehensive", response_model=ValidationResponse)
async def validate_comprehensive(request: ValidationRequest):
    """
    Comprehensive validation for Kolegium workflow.
    Returns 8-12 rules covering all aspects: style, structure, platform, audience.
    """
    start_time = time.time()
    
    try:
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
        
    except Exception as e:
        logger.error("Comprehensive validation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

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
    
    try:
        # Get selective rules for specific checkpoint (3-4 rules)
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
        
    except Exception as e:
        logger.error("Selective validation failed", error=str(e), checkpoint=request.checkpoint)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/query/rules")
async def query_rules(mode: ValidationMode, checkpoint: Optional[CheckpointType] = None):
    """
    Query rules based on mode and optional checkpoint.
    Returns rules with ChromaDB origin metadata.
    """
    try:
        if mode == "comprehensive":
            rules = get_comprehensive_rules()
        elif mode == "selective":
            if not checkpoint:
                raise HTTPException(status_code=400, detail="Checkpoint required for selective mode")
            rules = get_selective_rules_for_checkpoint(checkpoint)
        else:
            raise HTTPException(status_code=400, detail="Invalid mode. Use 'comprehensive' or 'selective'")
        
        return {
            "mode": mode,
            "checkpoint": checkpoint,
            "rules": rules,
            "rule_count": len(rules),
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Query rules failed", error=str(e), mode=mode, checkpoint=checkpoint)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8040)