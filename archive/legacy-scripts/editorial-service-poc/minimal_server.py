#!/usr/bin/env python3
"""
Minimal Editorial Service for testing - Pure HTTP server
"""

import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class EditorialServiceHandler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/health':
            self.send_health_response()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        if self.path == '/validate/comprehensive':
            self.handle_comprehensive_validation()
        elif self.path == '/validate/selective':
            self.handle_selective_validation()
        else:
            self.send_error(404, "Not Found")
    
    def send_health_response(self):
        """Health check endpoint"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "chromadb_connected": True,
            "cache_status": "ready", 
            "dual_workflow_ready": True
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(health_data).encode())
    
    def handle_comprehensive_validation(self):
        """Comprehensive validation - returns 11 rules"""
        start_time = time.time()
        
        # Parse request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            request_data = json.loads(post_data.decode())
        except:
            self.send_error(400, "Invalid JSON")
            return
        
        # Comprehensive rules (11 rules total)
        rules = [
            {
                "rule_id": "sty_con_001", "rule_name": "style_consistency", "rule_type": "style",
                "description": "Writing style consistent with brand guidelines", "severity": "high",
                "collection_source": "style_editorial_rules",
                "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            },
            {
                "rule_id": "ton_mat_001", "rule_name": "tone_match", "rule_type": "style",
                "description": "Tone matches publication requirements", "severity": "high",
                "collection_source": "style_editorial_rules",
                "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            },
            {
                "rule_id": "str_req_001", "rule_name": "structure_requirements", "rule_type": "structural",
                "description": "Content structure meets publication standards", "severity": "high",
                "collection_source": "style_editorial_rules",
                "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            },
            {
                "rule_id": "plt_opt_001", "rule_name": "platform_optimization", "rule_type": "platform",
                "description": "Content optimized for target platforms", "severity": "medium",
                "collection_source": "publication_platform_rules",
                "chromadb_origin_metadata": {"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
            },
            {
                "rule_id": "aud_tgt_001", "rule_name": "audience_targeting", "rule_type": "content",
                "description": "Content targets appropriate audience segment", "severity": "high",
                "collection_source": "publication_platform_rules",
                "chromadb_origin_metadata": {"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
            },
            {
                "rule_id": "qua_gat_001", "rule_name": "quality_gates", "rule_type": "quality",
                "description": "All quality gates and standards met", "severity": "high",
                "collection_source": "style_editorial_rules",
                "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            },
            {
                "rule_id": "hum_chk_001", "rule_name": "humanization_check", "rule_type": "quality",
                "description": "Content passes AI detection avoidance checks", "severity": "high",
                "collection_source": "style_editorial_rules",
                "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            },
            {
                "rule_id": "seo_opt_001", "rule_name": "seo_optimization", "rule_type": "platform",
                "description": "SEO best practices implemented", "severity": "medium",
                "collection_source": "publication_platform_rules",
                "chromadb_origin_metadata": {"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
            },
            {
                "rule_id": "eng_met_001", "rule_name": "engagement_metrics", "rule_type": "content",
                "description": "Content structured for high engagement", "severity": "medium",
                "collection_source": "publication_platform_rules",
                "chromadb_origin_metadata": {"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
            },
            {
                "rule_id": "bra_ali_001", "rule_name": "brand_alignment", "rule_type": "style",
                "description": "Content aligns with brand voice and values", "severity": "high",
                "collection_source": "style_editorial_rules",
                "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            },
            {
                "rule_id": "com_pli_001", "rule_name": "compliance_check", "rule_type": "quality",
                "description": "Content meets compliance and legal requirements", "severity": "high",
                "collection_source": "style_editorial_rules",
                "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
            }
        ]
        
        processing_time = (time.time() - start_time) * 1000
        
        response_data = {
            "mode": "comprehensive",
            "checkpoint": None,
            "rules_applied": rules,
            "rule_count": len(rules),
            "processing_time_ms": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())
    
    def handle_selective_validation(self):
        """Selective validation - returns 3 rules per checkpoint"""
        start_time = time.time()
        
        # Parse request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            request_data = json.loads(post_data.decode())
            checkpoint = request_data.get('checkpoint')
        except:
            self.send_error(400, "Invalid JSON")
            return
        
        if not checkpoint:
            self.send_error(400, "Checkpoint required for selective validation")
            return
        
        # Checkpoint-specific rules (3 each)
        checkpoint_rules = {
            "pre-writing": [
                {
                    "rule_id": "pub_type_001", "rule_name": "publication_type_match", "rule_type": "structural",
                    "description": "Content matches selected publication type requirements", "severity": "high",
                    "collection_source": "publication_platform_rules",
                    "chromadb_origin_metadata": {"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
                },
                {
                    "rule_id": "aud_tgt_001", "rule_name": "audience_targeting", "rule_type": "content",
                    "description": "Content targets appropriate audience segment", "severity": "high",
                    "collection_source": "publication_platform_rules",
                    "chromadb_origin_metadata": {"collection": "publication_platform_rules", "query_timestamp": datetime.utcnow().isoformat()}
                },
                {
                    "rule_id": "str_bas_001", "rule_name": "structure_basic", "rule_type": "structural",
                    "description": "Basic content structure requirements met", "severity": "medium",
                    "collection_source": "style_editorial_rules",
                    "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
                }
            ],
            "mid-writing": [
                {
                    "rule_id": "sty_con_001", "rule_name": "style_consistency", "rule_type": "style",
                    "description": "Writing style consistent with brand guidelines", "severity": "high",
                    "collection_source": "style_editorial_rules",
                    "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
                },
                {
                    "rule_id": "ton_mat_001", "rule_name": "tone_match", "rule_type": "style",
                    "description": "Tone matches publication requirements", "severity": "high",
                    "collection_source": "style_editorial_rules",
                    "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
                },
                {
                    "rule_id": "flw_qua_001", "rule_name": "flow_quality", "rule_type": "content",
                    "description": "Content flow and readability standards met", "severity": "medium",
                    "collection_source": "style_editorial_rules",
                    "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
                }
            ],
            "post-writing": [
                {
                    "rule_id": "hum_chk_001", "rule_name": "humanization_check", "rule_type": "quality",
                    "description": "Content passes AI detection avoidance checks", "severity": "high",
                    "collection_source": "style_editorial_rules",
                    "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
                },
                {
                    "rule_id": "aid_avo_001", "rule_name": "ai_detection_avoid", "rule_type": "quality",
                    "description": "Anti-AI detection patterns implemented", "severity": "high",
                    "collection_source": "style_editorial_rules",
                    "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
                },
                {
                    "rule_id": "fin_pol_001", "rule_name": "final_polish", "rule_type": "quality",
                    "description": "Final editorial polish and quality gates passed", "severity": "medium",
                    "collection_source": "style_editorial_rules",
                    "chromadb_origin_metadata": {"collection": "style_editorial_rules", "query_timestamp": datetime.utcnow().isoformat()}
                }
            ]
        }
        
        rules = checkpoint_rules.get(checkpoint, [])
        processing_time = (time.time() - start_time) * 1000
        
        response_data = {
            "mode": "selective",
            "checkpoint": checkpoint,
            "rules_applied": rules,
            "rule_count": len(rules),
            "processing_time_ms": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())

def run_server():
    server_address = ('', 8040)
    httpd = HTTPServer(server_address, EditorialServiceHandler)
    print("🚀 Editorial Service running on http://localhost:8040")
    print("🏥 Health endpoint: http://localhost:8040/health")
    print("📝 Comprehensive: POST /validate/comprehensive")
    print("✅ Selective: POST /validate/selective")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()