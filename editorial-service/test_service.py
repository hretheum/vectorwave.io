#!/usr/bin/env python3
"""
Simple test script to validate Editorial Service functionality without full dependencies
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List

def test_health_endpoint():
    """Test health endpoint returns 200"""
    try:
        response = urllib.request.urlopen("http://localhost:8040/health", timeout=10)
        if response.status == 200:
            print("✅ Health endpoint: PASSED")
            return True
        else:
            print(f"❌ Health endpoint: FAILED (status {response.status})")
            return False
    except Exception as e:
        print(f"❌ Health endpoint: FAILED ({str(e)})")
        return False

def test_comprehensive_validation():
    """Test comprehensive validation endpoint"""
    payload = {
        "content": "test content for validation",
        "mode": "comprehensive"
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(
            "http://localhost:8040/validate/comprehensive",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(request, timeout=10)
        
        if response.status == 200:
            result = json.loads(response.read())
            rule_count = result.get('rule_count', 0)
            if 8 <= rule_count <= 12:
                print(f"✅ Comprehensive validation: PASSED ({rule_count} rules)")
                return True
            else:
                print(f"❌ Comprehensive validation: FAILED (expected 8-12 rules, got {rule_count})")
                return False
        else:
            print(f"❌ Comprehensive validation: FAILED (status {response.status})")
            return False
    except Exception as e:
        print(f"❌ Comprehensive validation: FAILED ({str(e)})")
        return False

def test_selective_validation():
    """Test selective validation endpoint"""
    checkpoints = ["pre-writing", "mid-writing", "post-writing"]
    
    for checkpoint in checkpoints:
        payload = {
            "content": "test content for validation",
            "mode": "selective",
            "checkpoint": checkpoint
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            request = urllib.request.Request(
                "http://localhost:8040/validate/selective",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            response = urllib.request.urlopen(request, timeout=10)
            
            if response.status == 200:
                result = json.loads(response.read())
                rule_count = result.get('rule_count', 0)
                if 3 <= rule_count <= 4:
                    print(f"✅ Selective validation ({checkpoint}): PASSED ({rule_count} rules)")
                else:
                    print(f"❌ Selective validation ({checkpoint}): FAILED (expected 3-4 rules, got {rule_count})")
                    return False
            else:
                print(f"❌ Selective validation ({checkpoint}): FAILED (status {response.status})")
                return False
        except Exception as e:
            print(f"❌ Selective validation ({checkpoint}): FAILED ({str(e)})")
            return False
    
    return True

def test_performance():
    """Test that response times meet requirements"""
    start_time = time.time()
    
    payload = {
        "content": "test content",
        "mode": "comprehensive"
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(
            "http://localhost:8040/validate/comprehensive",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(request, timeout=10)
        elapsed = (time.time() - start_time) * 1000
        
        if response.status == 200 and elapsed < 200:
            print(f"✅ Performance test: PASSED ({elapsed:.1f}ms)")
            return True
        else:
            print(f"❌ Performance test: FAILED ({elapsed:.1f}ms, expected <200ms)")
            return False
    except Exception as e:
        print(f"❌ Performance test: FAILED ({str(e)})")
        return False

def main():
    print("🧪 Testing Editorial Service - Dual Workflow Support")
    print("=" * 60)
    
    # Wait for service to be ready
    print("⏳ Waiting for service to start...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Comprehensive Validation", test_comprehensive_validation), 
        ("Selective Validation", test_selective_validation),
        ("Performance Test", test_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        if test_func():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests PASSED! Editorial Service is working correctly.")
        return True
    else:
        print("💥 Some tests FAILED. Check the service implementation.")
        return False

if __name__ == "__main__":
    exit(0 if main() else 1)