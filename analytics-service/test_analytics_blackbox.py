#!/usr/bin/env python3
"""
Test script for Analytics Blackbox Service
Validates placeholder functionality and API endpoints
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8081"

async def test_health_check():
    """Test health check endpoint"""
    print("🏥 Testing Analytics Blackbox health check...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data['status']}")
                print(f"   Placeholder mode: {data['placeholder_mode']}")
                print(f"   Future capabilities: {len(data['future_capabilities'])}")
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
                print(f"   Status: {data['status']}")
                print(f"   Future capabilities: {len(data['future_capabilities'])}")
                print(f"   Total tracked: {data['total_tracked_publications']}")
                return True
            else:
                print(f"❌ Service info failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Service info error: {e}")
            return False

async def test_track_publication():
    """Test publication tracking endpoint"""
    print("📊 Testing publication tracking...")
    
    test_metrics = {
        "publication_id": "test-pub-001",
        "platform": "linkedin",
        "metrics": {
            "views": 1250,
            "likes": 89,
            "shares": 12,
            "comments": 7,
            "engagement_rate": 0.086
        },
        "user_id": "test-user-123",
        "content_type": "article"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/track-publication",
                json=test_metrics,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Publication tracking successful!")
                print(f"   Publication ID: {data['publication_id']}")
                print(f"   Platform: {data['platform']}")
                print(f"   Status: {data['status']}")
                print(f"   Tracked metrics: {data['tracked_metrics']}")
                print(f"   Future features: {len(data['future_features'])}")
                return True
            else:
                print(f"❌ Publication tracking failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Publication tracking error: {e}")
            return False

async def test_user_insights():
    """Test user insights endpoint"""
    print("🔍 Testing user insights...")
    
    test_user_id = "test-user-123"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/insights/{test_user_id}", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User insights retrieved successfully!")
                print(f"   User ID: {data['user_id']}")
                print(f"   Publications tracked: {data['insights']['publications_tracked']}")
                print(f"   Platforms active: {data['insights']['platforms_active']}")
                print(f"   Recommendations: {len(data['placeholder_recommendations'])}")
                print(f"   Future features: {len(data['future_features'])}")
                return True
            else:
                print(f"❌ User insights failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ User insights error: {e}")
            return False

async def test_platform_analytics():
    """Test platform analytics endpoint"""
    print("📈 Testing platform analytics...")
    
    test_platform = "linkedin"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/analytics/{test_platform}", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Platform analytics retrieved successfully!")
                print(f"   Platform: {data['platform']}")
                print(f"   Total publications: {data['total_publications']}")
                print(f"   Placeholder note: {data['placeholder_note']}")
                return True
            else:
                print(f"❌ Platform analytics failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Platform analytics error: {e}")
            return False

async def test_global_stats():
    """Test global statistics endpoint"""
    print("📊 Testing global statistics...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/stats", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Global stats retrieved successfully!")
                print(f"   Service: {data['service']}")
                print(f"   Total tracked: {data['global_statistics']['total_publications_tracked']}")
                print(f"   Platforms supported: {data['global_statistics']['platforms_supported']}")
                print(f"   Uptime hours: {data['global_statistics']['uptime_hours']}")
                print(f"   Future metrics: {len(data['future_metrics'])}")
                return True
            else:
                print(f"❌ Global stats failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Global stats error: {e}")
            return False

async def test_multiple_publications():
    """Test tracking multiple publications"""
    print("📚 Testing multiple publication tracking...")
    
    publications = [
        {
            "publication_id": "test-pub-002",
            "platform": "twitter",
            "metrics": {"retweets": 45, "likes": 234, "replies": 12},
            "user_id": "test-user-456",
            "content_type": "thread"
        },
        {
            "publication_id": "test-pub-003", 
            "platform": "beehiiv",
            "metrics": {"opens": 892, "clicks": 78, "unsubscribes": 2},
            "user_id": "test-user-123",
            "content_type": "newsletter"
        }
    ]
    
    success_count = 0
    async with httpx.AsyncClient() as client:
        for pub in publications:
            try:
                response = await client.post(f"{BASE_URL}/track-publication", json=pub, timeout=10.0)
                if response.status_code == 200:
                    success_count += 1
            except Exception as e:
                print(f"❌ Error tracking {pub['publication_id']}: {e}")
    
    print(f"✅ Multiple publication tracking: {success_count}/{len(publications)} successful")
    return success_count == len(publications)

async def test_invalid_platform():
    """Test invalid platform handling"""
    print("⚠️ Testing invalid platform handling...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/analytics/invalid-platform", timeout=5.0)
            
            if response.status_code == 404:
                print("✅ Invalid platform correctly handled with 404")
                return True
            else:
                print(f"❌ Expected 404, got: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Invalid platform test error: {e}")
            return False

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
    print("🚀 Starting Analytics Blackbox Service Tests")
    print("=" * 60)
    
    results = []
    
    # Test health check
    results.append(await test_health_check())
    
    # Test service info
    results.append(await test_service_info())
    
    # Test publication tracking
    results.append(await test_track_publication())
    
    # Test user insights
    results.append(await test_user_insights())
    
    # Test platform analytics
    results.append(await test_platform_analytics())
    
    # Test global stats
    results.append(await test_global_stats())
    
    # Test multiple publications
    results.append(await test_multiple_publications())
    
    # Test invalid platform
    results.append(await test_invalid_platform())
    
    # Test documentation
    results.append(await test_docs_endpoint())
    
    print("=" * 60)
    print(f"📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Analytics Blackbox Service is working correctly.")
        print("✅ Placeholder functionality ready for future analytics implementation.")
        return True
    else:
        print("❌ Some tests failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)