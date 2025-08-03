#!/usr/bin/env python3
"""
Comprehensive test runner for Knowledge Base
Runs all test suites and generates detailed reports
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any


class TestRunner:
    """Comprehensive test runner with reporting"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.results = {}
        
    def run_command(self, cmd: List[str], description: str) -> Dict[str, Any]:
        """Run a command and capture results"""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"Exit code: {result.returncode}")
            print(f"Duration: {duration:.2f} seconds")
            
            if result.stdout:
                print(f"\nSTDOUT:\n{result.stdout}")
            
            if result.stderr:
                print(f"\nSTDERR:\n{result.stderr}")
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            print(f"Command timed out after 5 minutes")
            return {
                "success": False,
                "exit_code": -1,
                "duration": 300,
                "stdout": "",
                "stderr": "Command timed out"
            }
        except Exception as e:
            print(f"Command failed with error: {e}")
            return {
                "success": False,
                "exit_code": -1,
                "duration": 0,
                "stdout": "",
                "stderr": str(e)
            }
    
    def run_unit_tests(self, coverage: bool = True) -> Dict[str, Any]:
        """Run unit tests with coverage"""
        cmd = ["python3", "-m", "pytest", "tests/unit/", "-v", "--tb=short"]
        
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=html:htmlcov",
                "--cov-report=term-missing",
                "--cov-report=xml",
                "--cov-fail-under=80"
            ])
        
        cmd.extend(["-m", "unit"])
        
        return self.run_command(cmd, "Unit Tests with Coverage")
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        cmd = [
            "python3", "-m", "pytest", 
            "tests/integration/", 
            "-v", "--tb=short",
            "-m", "integration"
        ]
        
        return self.run_command(cmd, "Integration Tests")
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        cmd = [
            "python3", "-m", "pytest", 
            "tests/performance/", 
            "-v", "--tb=short",
            "-m", "performance",
            "--benchmark-only",
            "--benchmark-sort=mean"
        ]
        
        return self.run_command(cmd, "Performance Tests")
    
    def run_edge_case_tests(self) -> Dict[str, Any]:
        """Run edge case tests"""
        cmd = [
            "python3", "-m", "pytest", 
            "tests/edge_cases/", 
            "-v", "--tb=short",
            "-m", "edge_case"
        ]
        
        return self.run_command(cmd, "Edge Case Tests")
    
    def run_api_tests(self) -> Dict[str, Any]:
        """Run API integration tests"""
        cmd = [
            "python3", "-m", "pytest", 
            "tests/integration/test_api.py", 
            "-v", "--tb=short"
        ]
        
        return self.run_command(cmd, "API Tests")
    
    def run_parallel_tests(self) -> Dict[str, Any]:
        """Run tests in parallel for speed"""
        cmd = [
            "python3", "-m", "pytest", 
            "tests/unit/",
            "-v", "--tb=short",
            "-n", "auto",  # Automatic worker count
            "-m", "unit and not slow"
        ]
        
        return self.run_command(cmd, "Parallel Unit Tests")
    
    def run_slow_tests(self) -> Dict[str, Any]:
        """Run slow/long-running tests"""
        cmd = [
            "python3", "-m", "pytest", 
            "tests/",
            "-v", "--tb=short",
            "-m", "slow",
            "--timeout=600"  # 10 minute timeout for slow tests
        ]
        
        return self.run_command(cmd, "Slow Tests")
    
    def run_memory_profiling(self) -> Dict[str, Any]:
        """Run tests with memory profiling"""
        cmd = [
            "python3", "-m", "pytest", 
            "tests/performance/",
            "-v", "--tb=short",
            "-m", "performance",
            "--profile"
        ]
        
        return self.run_command(cmd, "Memory Profiling Tests")
    
    def check_code_quality(self) -> Dict[str, Any]:
        """Run code quality checks"""
        print(f"\n{'='*60}")
        print("Running Code Quality Checks")
        print(f"{'='*60}")
        
        results = {}
        
        # Black formatting check
        black_result = self.run_command(
            ["python3", "-m", "black", "--check", "src/", "tests/"],
            "Black Format Check"
        )
        results["black"] = black_result
        
        # Flake8 linting
        flake8_result = self.run_command(
            ["python3", "-m", "flake8", "src/", "tests/"],
            "Flake8 Linting"
        )
        results["flake8"] = flake8_result
        
        # MyPy type checking
        mypy_result = self.run_command(
            ["python3", "-m", "mypy", "src/"],
            "MyPy Type Checking"
        )
        results["mypy"] = mypy_result
        
        # Import sorting check
        isort_result = self.run_command(
            ["python3", "-m", "isort", "--check-only", "src/", "tests/"],
            "Import Sorting Check"
        )
        results["isort"] = isort_result
        
        overall_success = all(r["success"] for r in results.values())
        
        return {
            "success": overall_success,
            "results": results
        }
    
    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE TEST REPORT")
        print(f"{'='*80}")
        
        total_duration = sum(r.get("duration", 0) for r in self.results.values() if isinstance(r, dict))
        successful_suites = sum(1 for r in self.results.values() if isinstance(r, dict) and r.get("success", False))
        total_suites = len([r for r in self.results.values() if isinstance(r, dict)])
        
        print(f"Total test suites: {total_suites}")
        print(f"Successful suites: {successful_suites}")
        print(f"Failed suites: {total_suites - successful_suites}")
        print(f"Total duration: {total_duration:.2f} seconds")
        print(f"Success rate: {(successful_suites/total_suites)*100:.1f}%")
        
        print(f"\nDetailed Results:")
        print(f"{'-'*80}")
        
        for suite_name, result in self.results.items():
            if isinstance(result, dict):
                status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
                duration = result.get("duration", 0)
                print(f"{suite_name:<30} {status:<10} {duration:>8.2f}s")
        
        # Coverage summary
        coverage_file = self.base_dir / "htmlcov" / "index.html"
        if coverage_file.exists():
            print(f"\n📊 Coverage report generated: {coverage_file}")
        
        # Performance summary
        if "performance" in self.results:
            print(f"\n⚡ Performance test results available")
        
        print(f"\n📋 Full logs and reports saved in test outputs")
        
        # Exit with error code if any tests failed
        if successful_suites < total_suites:
            print(f"\n❌ Some test suites failed. Check the logs above.")
            sys.exit(1)
        else:
            print(f"\n✅ All test suites passed!")
    
    def run_all_tests(self, 
                     include_performance: bool = True,
                     include_slow: bool = False,
                     include_quality: bool = True,
                     parallel: bool = False) -> None:
        """Run all test suites"""
        
        print("Starting comprehensive test suite for Knowledge Base")
        print(f"Base directory: {self.base_dir}")
        
        # Core test suites
        if parallel:
            self.results["parallel_unit"] = self.run_parallel_tests()
        else:
            self.results["unit"] = self.run_unit_tests()
        
        self.results["integration"] = self.run_integration_tests()
        self.results["edge_cases"] = self.run_edge_case_tests()
        self.results["api"] = self.run_api_tests()
        
        # Optional test suites
        if include_performance:
            self.results["performance"] = self.run_performance_tests()
        
        if include_slow:
            self.results["slow"] = self.run_slow_tests()
        
        if include_quality:
            self.results["code_quality"] = self.check_code_quality()
        
        # Generate final report
        self.generate_report()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Knowledge Base Test Runner")
    
    parser.add_argument("--no-performance", action="store_true",
                       help="Skip performance tests")
    parser.add_argument("--include-slow", action="store_true",
                       help="Include slow/long-running tests")
    parser.add_argument("--no-quality", action="store_true",
                       help="Skip code quality checks")
    parser.add_argument("--parallel", action="store_true",
                       help="Run unit tests in parallel")
    parser.add_argument("--unit-only", action="store_true",
                       help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true",
                       help="Run only integration tests")
    parser.add_argument("--performance-only", action="store_true",
                       help="Run only performance tests")
    parser.add_argument("--api-only", action="store_true",
                       help="Run only API tests")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.unit_only:
        runner.results["unit"] = runner.run_unit_tests()
    elif args.integration_only:
        runner.results["integration"] = runner.run_integration_tests()
    elif args.performance_only:
        runner.results["performance"] = runner.run_performance_tests()
    elif args.api_only:
        runner.results["api"] = runner.run_api_tests()
    else:
        # Run all tests
        runner.run_all_tests(
            include_performance=not args.no_performance,
            include_slow=args.include_slow,
            include_quality=not args.no_quality,
            parallel=args.parallel
        )


if __name__ == "__main__":
    main()