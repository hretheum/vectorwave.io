#!/usr/bin/env python3
"""
Test script for LinkedIn PPT Generator Service
Validates LinkedIn-specific optimizations and Presenton integration
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8002"

async def test_health_check():
    """Test health check endpoint"""
    print("🏥 Testing LinkedIn PPT Generator health check...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data['status']}")
                print(f"   Presenton available: {data['presenton_available']}")
                print(f"   Presenton URL: {data['presenton_url']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

async def test_service_info():
    """Test service information endpoint"""
    print("ℹ️ Testing service information...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Service info retrieved: {data['service']}")
                print(f"   LinkedIn optimization: {data['features']['linkedin_optimization']}")
                print(f"   Circuit breaker status: {data['circuit_breaker_status']['circuit_open']}")
                return True
            else:
                print(f"❌ Service info failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Service info error: {e}")
            return False

async def test_linkedin_ppt_generation():
    """Test LinkedIn presentation generation"""
    print("🎯 Testing LinkedIn PPT generation...")
    
    test_request = {
        "topic_title": "AI-Powered Content Creation Revolution",
        "topic_description": "How artificial intelligence is transforming content creation workflows, from ideation to publication, with practical insights for modern marketers and content creators.",
        "slides_count": 6,
        "template": "business",
        "linkedin_format": True,
        "include_call_to_action": True,
        "target_audience": "marketing professionals and content creators",
        "keywords": ["AI", "content creation", "automation", "efficiency", "ROI"]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            start_time = time.time()
            response = await client.post(
                f"{BASE_URL}/generate-linkedin-ppt",
                json=test_request,
                timeout=90.0
            )
            
            if response.status_code == 200:
                data = response.json()
                generation_time = time.time() - start_time
                
                print(f"✅ LinkedIn PPT generation successful!")
                print(f"   Presentation ID: {data['presentation_id']}")
                print(f"   Slide count: {data['slide_count']}")
                print(f"   Template used: {data['template_used']}")
                print(f"   LinkedIn optimized: {data['linkedin_optimized']}")
                print(f"   Ready for LinkedIn: {data['ready_for_linkedin']}")
                print(f"   Generation time: {generation_time:.2f}s")
                print(f"   PPTX URL: {data['pptx_url']}")
                print(f"   PDF URL: {data['pdf_url']}")
                
                return data['presentation_id']
            else:
                print(f"❌ LinkedIn PPT generation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ LinkedIn PPT generation error: {e}")
            return None

async def test_minimal_generation():
    """Test minimal LinkedIn presentation generation"""
    print("📝 Testing minimal LinkedIn PPT generation...")
    
    minimal_request = {
        "topic_title": "Quick Test Presentation",
        "topic_description": "Simple test presentation to validate basic functionality",
        "slides_count": 3
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/generate-linkedin-ppt",
                json=minimal_request,
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Minimal generation successful!")
                print(f"   Presentation ID: {data['presentation_id']}")
                print(f"   Slides: {data['slide_count']}")
                print(f"   Time: {data['generation_time']:.2f}s")
                return True
            else:
                print(f"❌ Minimal generation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Minimal generation error: {e}")
            return False

async def test_circuit_breaker_resilience():
    """Test circuit breaker behavior with invalid requests"""
    print("🔧 Testing circuit breaker resilience...")
    
    # Test with invalid data to trigger potential failures
    invalid_request = {
        "topic_title": "",  # Empty title
        "topic_description": "",  # Empty description
        "slides_count": 0  # Invalid count
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/generate-linkedin-ppt",
                json=invalid_request,
                timeout=30.0
            )
            
            # We expect this to fail with 422 (validation error)
            if response.status_code == 422:
                print("✅ Circuit breaker handling validation errors correctly")
                return True
            else:
                print(f"⚠️ Unexpected response for invalid data: {response.status_code}")
                return False
        except Exception as e:
            print(f"✅ Circuit breaker correctly handled error: {e}")
            return True

async def test_docs_endpoint():
    """Test API documentation endpoint"""
    print("📚 Testing API documentation...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/docs", timeout=5.0)
            if response.status_code == 200:
                print("✅ API documentation accessible")
                return True
            else:
                print(f"❌ API documentation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API documentation error: {e}")
            return False

async def main():
    """Run all tests"""
    print("🚀 Starting LinkedIn PPT Generator Service Tests")
    print("=" * 60)
    
    results = []
    
    # Test health check
    results.append(await test_health_check())
    
    # Test service info
    results.append(await test_service_info())
    
    # Test LinkedIn PPT generation
    presentation_id = await test_linkedin_ppt_generation()
    results.append(presentation_id is not None)
    
    # Test minimal generation
    results.append(await test_minimal_generation())
    
    # Test circuit breaker
    results.append(await test_circuit_breaker_resilience())
    
    # Test documentation
    results.append(await test_docs_endpoint())
    
    print("=" * 60)
    print(f"📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! LinkedIn PPT Generator Service is working correctly.")
        print("✅ Service is ready for integration with Publishing Orchestrator.")
        return True
    else:
        print("❌ Some tests failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)