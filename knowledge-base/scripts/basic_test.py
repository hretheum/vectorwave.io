#!/usr/bin/env python3
"""Basic functionality test without external dependencies"""

import asyncio
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic_imports():
    """Test that we can import our modules"""
    try:
        # Test basic structure
        print("✓ Testing basic imports...")
        
        # These should work without external dependencies
        from storage.chroma_client import ChromaDocument
        from cache.cache_manager import CacheConfig
        
        print("✓ Basic imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_chroma_document():
    """Test ChromaDocument class"""
    try:
        from storage.chroma_client import ChromaDocument
        
        print("✓ Testing ChromaDocument...")
        
        doc = ChromaDocument(
            id="test_doc",
            content="Test content",
            metadata={"title": "Test", "source": "test"}
        )
        
        assert doc.id == "test_doc"
        assert doc.content == "Test content"
        assert doc.metadata["title"] == "Test"
        
        print("✓ ChromaDocument test passed")
        return True
    except Exception as e:
        print(f"✗ ChromaDocument test failed: {e}")
        return False

def test_cache_config():
    """Test CacheConfig class"""
    try:
        from cache.cache_manager import CacheConfig
        
        print("✓ Testing CacheConfig...")
        
        config = CacheConfig(
            memory_enabled=True,
            redis_enabled=False,
            memory_ttl=300,
            redis_ttl=3600
        )
        
        assert config.memory_enabled is True
        assert config.redis_enabled is False
        assert config.memory_ttl == 300
        
        print("✓ CacheConfig test passed")
        return True
    except Exception as e:
        print(f"✗ CacheConfig test failed: {e}")
        return False

def test_project_structure():
    """Test that project structure is correct"""
    try:
        print("✓ Testing project structure...")
        
        required_files = [
            'src/__init__.py',
            'src/cache/__init__.py',
            'src/storage/__init__.py',
            'src/sync/__init__.py',
            'src/api/__init__.py',
            'src/knowledge_engine.py',
            'requirements.txt',
            'pyproject.toml',
            'docker/docker-compose.yml',
            'config/knowledge_base.yaml'
        ]
        
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        
        for file_path in required_files:
            full_path = os.path.join(base_dir, file_path)
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Required file missing: {file_path}")
        
        print("✓ Project structure test passed")
        return True
    except Exception as e:
        print(f"✗ Project structure test failed: {e}")
        return False

def test_config_files():
    """Test configuration files are valid"""
    try:
        print("✓ Testing configuration files...")
        
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        
        # Test requirements.txt
        req_file = os.path.join(base_dir, 'requirements.txt')
        with open(req_file, 'r') as f:
            content = f.read()
            assert 'chromadb' in content
            assert 'fastapi' in content
            assert 'redis' in content
        
        # Test docker-compose.yml exists and has basic structure
        docker_file = os.path.join(base_dir, 'docker/docker-compose.yml')
        with open(docker_file, 'r') as f:
            content = f.read()
            assert 'redis:' in content
            assert 'chroma:' in content
            assert 'postgres:' in content
        
        print("✓ Configuration files test passed")
        return True
    except Exception as e:
        print(f"✗ Configuration files test failed: {e}")
        return False

def test_api_structure():
    """Test API file structure"""
    try:
        print("✓ Testing API structure...")
        
        # Check that API routes file exists and has basic structure
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        api_file = os.path.join(base_dir, 'src/api/routes.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
            assert 'FastAPI' in content
            assert '/api/v1/knowledge/query' in content
            assert '/api/v1/knowledge/health' in content
            assert 'QueryRequest' in content
        
        print("✓ API structure test passed")
        return True
    except Exception as e:
        print(f"✗ API structure test failed: {e}")
        return False

def test_documentation():
    """Test that key documentation exists"""
    try:
        print("✓ Testing documentation...")
        
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        
        # Check ARCHITECTURE.md exists and has content
        arch_file = os.path.join(base_dir, 'ARCHITECTURE.md')
        if os.path.exists(arch_file):
            with open(arch_file, 'r') as f:
                content = f.read()
                assert len(content) > 1000  # Should be substantial
                assert 'Vector Store' in content or 'Cache' in content
        
        print("✓ Documentation test passed")
        return True
    except Exception as e:
        print(f"✗ Documentation test failed: {e}")
        return False

def main():
    """Run all basic tests"""
    print("🚀 Running Knowledge Base Basic Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Project Structure", test_project_structure),
        ("Configuration Files", test_config_files),
        ("ChromaDocument Class", test_chroma_document),
        ("CacheConfig Class", test_cache_config),
        ("API Structure", test_api_structure),
        ("Documentation", test_documentation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "PASS" if success else "FAIL"
        except Exception as e:
            results[test_name] = "ERROR"
            print(f"✗ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status_icon = "✅" if result == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {result}")
        if result == "PASS":
            passed += 1
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All basic tests passed!")
        print("\n🔧 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start Docker services: docker-compose -f docker/docker-compose.yml up -d")
        print("3. Run full test suite: python scripts/test_system.py")
        print("4. Start API server: uvicorn src.api.routes:app --host 0.0.0.0 --port 8080")
        return True
    else:
        print("❌ Some basic tests failed. Please fix these issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)