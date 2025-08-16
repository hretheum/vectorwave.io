"""
Circuit Breaker implementation for Gamma PPT Generator Service
Provides resilience for Gamma.app API calls
"""

import time
import logging
from typing import Any, Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, rejecting calls
    HALF_OPEN = "HALF_OPEN"  # Testing if service is back


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class GammaCircuitBreaker:
    """
    Circuit breaker specifically designed for Gamma.app API calls
    Implements more conservative thresholds for external paid API
    """
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 120, 
                 success_threshold: int = 2):
        """
        Initialize circuit breaker for Gamma API
        
        Args:
            failure_threshold: Number of failures before opening circuit (lower for paid API)
            recovery_timeout: Seconds to wait before attempting reset (longer for external service)
            success_threshold: Consecutive successes needed to close circuit from half-open
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        # State tracking
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        
        # Per-service tracking
        self.service_states = {}
        
        # Gamma-specific tracking
        self.api_call_count = 0
        self.cost_tracking = 0.0
        
        logger.info(f"🔌 Gamma Circuit Breaker initialized (threshold: {failure_threshold}, recovery: {recovery_timeout}s)")
    
    async def call_with_circuit_breaker(self, service_name: str, operation: Callable, 
                                       *args, **kwargs) -> Any:
        """
        Execute Gamma API operation with circuit breaker protection
        
        Args:
            service_name: Name of the service ("gamma_api")
            operation: Async function to execute
            *args, **kwargs: Arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            CircuitBreakerOpenError: When circuit breaker is open
        """
        # Get or initialize service state
        if service_name not in self.service_states:
            self.service_states[service_name] = {
                "state": CircuitBreakerState.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "last_failure_time": None,
                "consecutive_failures": 0,
                "total_calls": 0,
                "successful_calls": 0
            }
        
        service_state = self.service_states[service_name]
        service_state["total_calls"] += 1
        self.api_call_count += 1
        
        # Check current state
        if service_state["state"] == CircuitBreakerState.OPEN:
            if self._should_attempt_reset(service_state):
                service_state["state"] = CircuitBreakerState.HALF_OPEN
                service_state["success_count"] = 0
                logger.info(f"🔄 Circuit breaker for {service_name} moved to HALF_OPEN (attempt recovery)")
            else:
                time_until_retry = self.recovery_timeout - (time.time() - service_state["last_failure_time"])
                raise CircuitBreakerOpenError(
                    f"Gamma.app API is currently unavailable (circuit breaker OPEN). "
                    f"Retry in {time_until_retry:.0f} seconds to avoid costs from failed requests."
                )
        
        # Execute operation
        try:
            logger.debug(f"🎨 Executing Gamma API call: {operation.__name__}")
            result = await operation(*args, **kwargs)
            
            # Operation successful
            await self._record_success(service_name, service_state)
            return result
            
        except Exception as e:
            # Operation failed
            await self._record_failure(service_name, service_state, e)
            raise
    
    def _should_attempt_reset(self, service_state: dict) -> bool:
        """Check if enough time has passed to attempt reset"""
        if service_state["last_failure_time"] is None:
            return True
        
        return (time.time() - service_state["last_failure_time"]) > self.recovery_timeout
    
    async def _record_success(self, service_name: str, service_state: dict):
        """Record a successful Gamma API operation"""
        service_state["successful_calls"] += 1
        service_state["consecutive_failures"] = 0
        
        if service_state["state"] == CircuitBreakerState.HALF_OPEN:
            service_state["success_count"] += 1
            
            if service_state["success_count"] >= self.success_threshold:
                # Reset circuit breaker to CLOSED
                service_state["state"] = CircuitBreakerState.CLOSED
                service_state["failure_count"] = 0
                service_state["success_count"] = 0
                service_state["last_failure_time"] = None
                
                success_rate = service_state["successful_calls"] / service_state["total_calls"] * 100
                logger.info(f"✅ Circuit breaker for {service_name} reset to CLOSED "
                           f"(success rate: {success_rate:.1f}%)")
        
        elif service_state["state"] == CircuitBreakerState.CLOSED:
            # Reset failure count on successful operation
            service_state["failure_count"] = 0
    
    async def _record_failure(self, service_name: str, service_state: dict, error: Exception):
        """Record a failed Gamma API operation"""
        service_state["failure_count"] += 1
        service_state["consecutive_failures"] += 1
        service_state["last_failure_time"] = time.time()
        
        # Log failure with context for paid API
        error_context = {
            "service": service_name,
            "consecutive_failures": service_state["consecutive_failures"],
            "total_calls": service_state["total_calls"],
            "failure_rate": service_state["failure_count"] / service_state["total_calls"] * 100
        }
        
        logger.warning(f"⚠️ Gamma API operation failed: {error} (context: {error_context})")
        
        # Check if we should open the circuit breaker
        if (service_state["failure_count"] >= self.failure_threshold and 
            service_state["state"] != CircuitBreakerState.OPEN):
            
            service_state["state"] = CircuitBreakerState.OPEN
            
            logger.error(f"🚨 Circuit breaker for {service_name} OPENED after {service_state['failure_count']} failures. "
                        f"This protects against wasted API costs. Recovery in {self.recovery_timeout} seconds.")
    
    def get_state(self, service_name: Optional[str] = None) -> dict:
        """Get current circuit breaker state(s) with Gamma-specific metrics"""
        if service_name:
            if service_name in self.service_states:
                state = self.service_states[service_name]
                return {
                    service_name: {
                        "state": state["state"],
                        "failure_count": state["failure_count"],
                        "success_count": state["success_count"],
                        "consecutive_failures": state["consecutive_failures"],
                        "total_calls": state["total_calls"],
                        "successful_calls": state["successful_calls"],
                        "success_rate": state["successful_calls"] / max(1, state["total_calls"]) * 100,
                        "last_failure_time": state["last_failure_time"]
                    }
                }
            else:
                return {service_name: {"state": "NOT_INITIALIZED"}}
        else:
            # Return all service states with metrics
            states = {}
            for service, state in self.service_states.items():
                states[service] = {
                    "state": state["state"],
                    "failure_count": state["failure_count"],
                    "success_count": state["success_count"],
                    "consecutive_failures": state["consecutive_failures"],
                    "total_calls": state["total_calls"],
                    "successful_calls": state["successful_calls"],
                    "success_rate": state["successful_calls"] / max(1, state["total_calls"]) * 100
                }
            return states
    
    def reset_circuit_breaker(self, service_name: str):
        """Manually reset circuit breaker for a service (admin function)"""
        if service_name in self.service_states:
            # Preserve call statistics but reset circuit state
            self.service_states[service_name].update({
                "state": CircuitBreakerState.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "consecutive_failures": 0,
                "last_failure_time": None
            })
            logger.info(f"🔄 Manually reset circuit breaker for {service_name}")
    
    def get_service_availability(self) -> dict:
        """Get availability status with cost protection context"""
        availability = {}
        
        for service_name, state in self.service_states.items():
            if state["state"] == CircuitBreakerState.CLOSED:
                availability[service_name] = {
                    "status": "available",
                    "context": "Normal operation - API calls allowed"
                }
            elif state["state"] == CircuitBreakerState.HALF_OPEN:
                availability[service_name] = {
                    "status": "testing",
                    "context": "Recovery testing - limited API calls"
                }
            else:
                time_until_retry = max(0, self.recovery_timeout - (time.time() - state["last_failure_time"]))
                availability[service_name] = {
                    "status": "unavailable",
                    "context": f"Protected mode - preventing wasted API costs. Retry in {time_until_retry:.0f}s"
                }
        
        return availability
    
    def get_cost_protection_stats(self) -> dict:
        """Get statistics about cost protection provided by circuit breaker"""
        total_prevented_calls = 0
        
        for state in self.service_states.values():
            if state["state"] == CircuitBreakerState.OPEN:
                # Estimate prevented calls during open period
                open_duration = time.time() - (state["last_failure_time"] or 0)
                estimated_call_rate = state["total_calls"] / max(3600, open_duration)  # calls per second
                prevented_calls = estimated_call_rate * min(open_duration, self.recovery_timeout)
                total_prevented_calls += max(0, prevented_calls)
        
        return {
            "total_api_calls": self.api_call_count,
            "estimated_prevented_calls": int(total_prevented_calls),
            "estimated_cost_savings": total_prevented_calls * 0.50,  # Assuming $0.50 per call
            "protection_active": any(s["state"] == CircuitBreakerState.OPEN for s in self.service_states.values())
        }