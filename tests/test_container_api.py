import requests
import pytest
import time

BASE_URL = "http://localhost:8003"

def wait_for_api(timeout=30):
    """Czekaj aż API będzie dostępne"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def test_container_health():
    """Test że kontener odpowiada"""
    assert wait_for_api(), "API nie odpowiada po 30 sekundach"
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_routing_original_content():
    """Test że ORIGINAL content pomija research"""
    payload = {
        "title": "My Personal AI Journey",
        "content_ownership": "ORIGINAL",
        "content_type": "STANDARD"
    }
    
    response = requests.post(f"{BASE_URL}/api/test-routing", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["route_decision"] == "skip_research_flow"
    assert data["skip_research"] == True

def test_routing_external_technical():
    """Test że EXTERNAL TECHNICAL idzie przez deep research"""
    payload = {
        "title": "Kubernetes Architecture Deep Dive",
        "content_ownership": "EXTERNAL",
        "content_type": "TECHNICAL"
    }
    
    response = requests.post(f"{BASE_URL}/api/test-routing", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["route_decision"] == "technical_deep_dive_flow"
    assert data["skip_research"] == False

def test_routing_viral_content():
    """Test że VIRAL content dostaje specjalne traktowanie"""
    payload = {
        "title": "10 AI Secrets That Will Shock You",
        "content_ownership": "EXTERNAL", 
        "content_type": "VIRAL",
        "platform": "Twitter"
    }
    
    response = requests.post(f"{BASE_URL}/api/test-routing", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["route_decision"] == "viral_engagement_flow"
    assert data["skip_research"] == False
    assert data["input"]["platform"] == "Twitter"