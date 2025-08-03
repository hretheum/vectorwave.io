#!/usr/bin/env python3
"""
Test structure validation script
Validates test structure and basic imports without running full test suite
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Set


class TestValidator:
    """Validates test structure and completeness"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.errors = []
        self.warnings = []
        self.stats = {
            "test_files": 0,
            "test_classes": 0,
            "test_methods": 0,
            "fixtures": 0,
            "imports": 0
        }
    
    def validate_test_structure(self) -> bool:
        """Validate overall test structure"""
        print("🔍 Validating test structure...")
        
        # Check required directories exist
        required_dirs = [
            "tests",
            "tests/unit",
            "tests/integration", 
            "tests/edge_cases",
            "tests/performance"
        ]
        
        for dir_path in required_dirs:
            full_path = self.base_dir / dir_path
            if not full_path.exists():
                self.errors.append(f"Missing required directory: {dir_path}")
            elif not full_path.is_dir():
                self.errors.append(f"Path exists but is not a directory: {dir_path}")
            else:
                print(f"✅ Found directory: {dir_path}")
        
        # Check required files exist
        required_files = [
            "tests/conftest.py",
            "tests/__init__.py",
            "pytest.ini",
            "test_requirements.txt"
        ]
        
        for file_path in required_files:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                self.errors.append(f"Missing required file: {file_path}")
            else:
                print(f"✅ Found file: {file_path}")
        
        return len(self.errors) == 0
    
    def analyze_test_file(self, file_path: Path) -> Dict:
        """Analyze a single test file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            analysis = {
                "classes": [],
                "functions": [],
                "fixtures": [],
                "imports": [],
                "decorators": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if node.name.startswith('Test'):
                        analysis["classes"].append(node.name)
                        self.stats["test_classes"] += 1
                
                elif isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_'):
                        analysis["functions"].append(node.name)
                        self.stats["test_methods"] += 1
                    
                    # Check for pytest fixtures
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == 'fixture':
                            analysis["fixtures"].append(node.name)
                            self.stats["fixtures"] += 1
                        elif isinstance(decorator, ast.Attribute) and decorator.attr == 'fixture':
                            analysis["fixtures"].append(node.name)
                            self.stats["fixtures"] += 1
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                        self.stats["imports"] += 1
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        analysis["imports"].append(f"{module}.{alias.name}")
                        self.stats["imports"] += 1
            
            return analysis
            
        except Exception as e:
            self.errors.append(f"Error analyzing {file_path}: {e}")
            return {}
    
    def validate_test_coverage(self) -> bool:
        """Validate test coverage of components"""
        print("\n📊 Validating test coverage...")
        
        # Components that should have tests
        expected_components = {
            "memory_cache": "tests/unit/test_memory_cache.py",
            "redis_cache": "tests/unit/test_redis_cache.py", 
            "cache_manager": "tests/unit/test_cache_manager.py",
            "chroma_client": "tests/unit/test_chroma_client.py",
            "knowledge_engine": "tests/unit/test_knowledge_engine.py",
            "api": "tests/integration/test_api.py",
            "end_to_end": "tests/integration/test_end_to_end.py",
            "edge_cases": "tests/edge_cases/test_edge_cases.py",
            "performance": "tests/performance/test_performance.py"
        }
        
        missing_tests = []
        for component, test_file in expected_components.items():
            full_path = self.base_dir / test_file
            if not full_path.exists():
                missing_tests.append(test_file)
            else:
                print(f"✅ Found test file: {test_file}")
        
        if missing_tests:
            for missing in missing_tests:
                self.errors.append(f"Missing test file: {missing}")
        
        return len(missing_tests) == 0
    
    def validate_test_quality(self) -> bool:
        """Validate test quality and patterns"""
        print("\n🔍 Validating test quality...")
        
        test_files = list(self.base_dir.glob("tests/**/*test_*.py"))
        
        for test_file in test_files:
            self.stats["test_files"] += 1
            analysis = self.analyze_test_file(test_file)
            
            # Check for test classes
            if not analysis.get("classes") and not analysis.get("functions"):
                self.warnings.append(f"No test classes or functions found in {test_file}")
            
            # Check for proper imports
            required_imports = ["pytest"]
            missing_imports = []
            
            for req_import in required_imports:
                if not any(req_import in imp for imp in analysis.get("imports", [])):
                    missing_imports.append(req_import)
            
            if missing_imports:
                self.warnings.append(f"Missing imports in {test_file}: {missing_imports}")
            
            print(f"📄 {test_file.name}: "
                  f"{len(analysis.get('classes', []))} classes, "
                  f"{len(analysis.get('functions', []))} test methods, "
                  f"{len(analysis.get('fixtures', []))} fixtures")
        
        return True
    
    def check_pytest_configuration(self) -> bool:
        """Check pytest configuration"""
        print("\n⚙️  Checking pytest configuration...")
        
        pytest_ini = self.base_dir / "pytest.ini"
        if pytest_ini.exists():
            try:
                with open(pytest_ini, 'r') as f:
                    content = f.read()
                
                # Check for important configurations
                required_configs = [
                    "testpaths",
                    "markers",
                    "addopts"
                ]
                
                for config in required_configs:
                    if config in content:
                        print(f"✅ Found pytest config: {config}")
                    else:
                        self.warnings.append(f"Missing pytest config: {config}")
                
            except Exception as e:
                self.errors.append(f"Error reading pytest.ini: {e}")
        
        return True
    
    def generate_report(self) -> None:
        """Generate validation report"""
        print(f"\n{'='*60}")
        print("TEST STRUCTURE VALIDATION REPORT")
        print(f"{'='*60}")
        
        # Statistics
        print(f"📊 Statistics:")
        print(f"  Test files: {self.stats['test_files']}")
        print(f"  Test classes: {self.stats['test_classes']}")
        print(f"  Test methods: {self.stats['test_methods']}")
        print(f"  Fixtures: {self.stats['fixtures']}")
        print(f"  Imports: {self.stats['imports']}")
        
        # Errors
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        # Warnings
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # Summary
        if not self.errors:
            print(f"\n✅ Test structure validation PASSED!")
            if self.warnings:
                print(f"   (with {len(self.warnings)} warnings)")
        else:
            print(f"\n❌ Test structure validation FAILED!")
            print(f"   {len(self.errors)} errors, {len(self.warnings)} warnings")
        
        # Coverage estimate
        if self.stats['test_methods'] > 0:
            estimated_coverage = min(100, (self.stats['test_methods'] / 50) * 100)  # Rough estimate
            print(f"\n📈 Estimated test coverage: ~{estimated_coverage:.0f}%")
            print(f"   Based on {self.stats['test_methods']} test methods")
    
    def validate_all(self) -> bool:
        """Run all validations"""
        print("🚀 Starting test structure validation...\n")
        
        validations = [
            ("Test Structure", self.validate_test_structure),
            ("Test Coverage", self.validate_test_coverage),
            ("Test Quality", self.validate_test_quality),
            ("Pytest Config", self.check_pytest_configuration)
        ]
        
        all_passed = True
        
        for name, validation_func in validations:
            try:
                result = validation_func()
                if not result:
                    all_passed = False
            except Exception as e:
                self.errors.append(f"Validation '{name}' failed: {e}")
                all_passed = False
        
        self.generate_report()
        return all_passed and len(self.errors) == 0


def main():
    """Main entry point"""
    validator = TestValidator()
    
    success = validator.validate_all()
    
    if success:
        print(f"\n🎉 All validations passed! Test structure is ready.")
        return 0
    else:
        print(f"\n💥 Some validations failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())