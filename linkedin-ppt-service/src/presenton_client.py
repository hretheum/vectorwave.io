#!/usr/bin/env python3
"""
Presenton Service HTTP Client with Circuit Breaker
Task 3.2.1: LinkedIn PPT Generator Service
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

logger = logging.getLogger(__name__)


class CircuitBreakerError(Exception):
    """Circuit breaker is open"""
    pass


class PresentonClient:
    """HTTP client for Presenton Service with circuit breaker pattern"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("PRESENTON_SERVICE_URL", "http://presenton:8089")
        self.timeout = float(os.getenv("PRESENTON_TIMEOUT", "60.0"))
        
        # Circuit breaker state
        self.failure_count = 0
        self.failure_threshold = 5
        self.circuit_open = False
        self.last_failure_time = 0
        self.recovery_timeout = 60  # seconds
        
        logger.info(f"PresentonClient initialized - URL: {self.base_url}")
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker should open/close"""
        import time
        
        current_time = time.time()
        
        if self.circuit_open:
            # Check if we can attempt recovery
            if current_time - self.last_failure_time > self.recovery_timeout:
                logger.info("🔄 Circuit breaker attempting recovery")
                self.circuit_open = False
                self.failure_count = 0
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN - too many failures")
    
    def _record_success(self):
        """Record successful request"""
        if self.failure_count > 0:
            logger.info(f"🎉 Presenton service recovered after {self.failure_count} failures")
        self.failure_count = 0
        self.circuit_open = False
    
    def _record_failure(self):
        """Record failed request"""
        import time
        
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            logger.error(f"🚨 Circuit breaker OPENED after {self.failure_count} failures")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def health_check(self) -> Dict[str, Any]:
        """Check Presenton service health"""
        self._check_circuit_breaker()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
                response.raise_for_status()
                result = response.json()
                
                self._record_success()
                return result
                
        except Exception as e:
            self._record_failure()
            logger.error(f"❌ Presenton health check failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def generate_presentation(
        self,
        prompt: str,
        slides_count: int = 5,
        template: str = "business",
        topic_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate presentation via Presenton service"""
        self._check_circuit_breaker()
        
        payload = {
            "prompt": prompt,
            "slides_count": slides_count,
            "template": template,
            "topic_title": topic_title or "LinkedIn Presentation"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                
                self._record_success()
                logger.info(f"✅ Presentation generated: {result['presentation_id']}")
                return result
                
        except Exception as e:
            self._record_failure()
            logger.error(f"❌ Presentation generation failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def get_service_info(self) -> Dict[str, Any]:
        """Get Presenton service information"""
        self._check_circuit_breaker()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/",
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                
                self._record_success()
                return result
                
        except Exception as e:
            self._record_failure()
            logger.error(f"❌ Service info request failed: {e}")
            raise
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "circuit_open": self.circuit_open,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout
        }