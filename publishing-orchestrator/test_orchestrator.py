#!/usr/bin/env python3
"""
Test script for Publishing Orchestrator API
Validates core functionality and integration points
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8050"

async def test_health_check():
    """Test health check endpoint"""
    print("🏥 Testing health check...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data['status']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

async def test_metrics():
    """Test metrics endpoint"""
    print("📊 Testing metrics endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/metrics", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Metrics endpoint working: {data['service']}")
                print(f"   Total publications: {data['total_publications']}")
                return True
            else:
                print(f"❌ Metrics failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Metrics error: {e}")
            return False

async def test_simple_publication():
    """Test simple publication endpoint"""
    print("🧪 Testing simple publication...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/test/simple", timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Simple publication successful!")
                print(f"   Publication ID: {data['publication_id']}")
                print(f"   Status: {data['status']}")
                print(f"   Success count: {data['success_count']}")
                print(f"   Generation time: {data['generation_time']:.2f}s")
                return data['publication_id']
            else:
                print(f"❌ Simple publication failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Simple publication error: {e}")
            return None

async def test_custom_publication():
    """Test custom publication with multiple platforms"""
    print("🎯 Testing custom multi-platform publication...")
    
    payload = {
        "topic": {
            "title": "AI-Powered Publishing Orchestrator",
            "description": "Advanced multi-platform content distribution system with Editorial Service integration",
            "keywords": ["AI", "automation", "publishing", "orchestrator"],
            "target_audience": "developers",
            "content_type": "article"
        },
        "platforms": {
            "linkedin": {
                "enabled": True,
                "account_id": "test_linkedin",
                "direct_content": True,
                "options": {"format": "professional"}
            },
            "twitter": {
                "enabled": True,
                "account_id": "test_twitter", 
                "direct_content": True,
                "options": {"thread": True}
            }
        },
        "global_options": {
            "priority": "high",
            "test_mode": True
        },
        "request_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/publish", 
                json=payload, 
                timeout=60.0
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Custom publication successful!")
                print(f"   Publication ID: {data['publication_id']}")
                print(f"   Request ID: {data['request_id']}")
                print(f"   Status: {data['status']}")
                print(f"   Success count: {data['success_count']}")
                print(f"   Error count: {data['error_count']}")
                print(f"   Generation time: {data['generation_time']:.2f}s")
                
                for platform, content in data['platform_content'].items():
                    print(f"   📱 {platform}: quality={content['quality_score']:.2f}, "
                          f"compliant={content['validation_compliant']}, "
                          f"time={content['generation_time']:.2f}s")
                
                return data['publication_id']
            else:
                print(f"❌ Custom publication failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Custom publication error: {e}")
            return None

async def test_publication_status(publication_id: str):
    """Test publication status endpoint"""
    if not publication_id:
        return False
        
    print(f"📋 Testing publication status for {publication_id}...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/publication/{publication_id}", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Publication status retrieved successfully!")
                print(f"   Status: {data['status']}")
                print(f"   Total platforms: {data['total_platforms']}")
                print(f"   Successful platforms: {data['successful_platforms']}")
                print(f"   Failed platforms: {data['failed_platforms']}")
                
                for platform, status in data['platform_statuses'].items():
                    print(f"   📱 {platform}: {status['status']} "
                          f"(quality: {status['quality_score']:.2f})")
                
                return True
            else:
                print(f"❌ Publication status failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Publication status error: {e}")
            return False

async def test_publications_list():
    """Test publications list endpoint"""
    print("📝 Testing publications list...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/publications?limit=5", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Publications list retrieved successfully!")
                print(f"   Total publications: {data['total']}")
                print(f"   Showing: {len(data['publications'])}")
                
                for pub in data['publications'][:2]:  # Show first 2
                    print(f"   📄 {pub['publication_id']}: {pub['status']} "
                          f"({pub['success_count']} successful)")
                
                return True
            else:
                print(f"❌ Publications list failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Publications list error: {e}")
            return False

async def main():
    """Run all tests"""
    print("🚀 Starting Publishing Orchestrator API Tests")
    print("=" * 60)
    
    results = []
    
    # Test health check
    results.append(await test_health_check())
    
    # Test metrics
    results.append(await test_metrics())
    
    # Test simple publication
    publication_id = await test_simple_publication()
    results.append(publication_id is not None)
    
    # Test custom publication
    custom_pub_id = await test_custom_publication()
    results.append(custom_pub_id is not None)
    
    # Test publication status
    if publication_id:
        results.append(await test_publication_status(publication_id))
    
    # Test publications list
    results.append(await test_publications_list())
    
    print("=" * 60)
    print(f"📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Publishing Orchestrator API is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)