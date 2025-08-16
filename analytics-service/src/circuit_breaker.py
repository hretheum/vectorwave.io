"""
Circuit Breaker implementation for Analytics Service
Provides resilience for external API calls and service dependencies
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


class AnalyticsCircuitBreaker:
    """
    Circuit breaker for external analytics API calls
    Implements the circuit breaker pattern for resilience
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, 
                 success_threshold: int = 3):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting reset
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
    
    async def call_with_circuit_breaker(self, service_name: str, operation: Callable, 
                                       *args, **kwargs) -> Any:
        """
        Execute operation with circuit breaker protection
        
        Args:
            service_name: Name of the service (e.g., "ghost_api", "typefully_proxy")
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
                "last_failure_time": None
            }
        
        service_state = self.service_states[service_name]
        
        # Check current state
        if service_state["state"] == CircuitBreakerState.OPEN:
            if self._should_attempt_reset(service_state):
                service_state["state"] = CircuitBreakerState.HALF_OPEN
                service_state["success_count"] = 0
                logger.info(f"🔄 Circuit breaker for {service_name} moved to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(
                    f"{service_name} service is currently unavailable (circuit breaker OPEN)"
                )
        
        # Execute operation
        try:
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
        """Record a successful operation"""
        if service_state["state"] == CircuitBreakerState.HALF_OPEN:
            service_state["success_count"] += 1
            
            if service_state["success_count"] >= self.success_threshold:
                # Reset circuit breaker to CLOSED
                service_state["state"] = CircuitBreakerState.CLOSED
                service_state["failure_count"] = 0
                service_state["success_count"] = 0
                service_state["last_failure_time"] = None
                
                logger.info(f"✅ Circuit breaker for {service_name} reset to CLOSED")
        
        elif service_state["state"] == CircuitBreakerState.CLOSED:
            # Reset failure count on successful operation
            service_state["failure_count"] = 0
    
    async def _record_failure(self, service_name: str, service_state: dict, error: Exception):
        """Record a failed operation"""
        service_state["failure_count"] += 1
        service_state["last_failure_time"] = time.time()
        
        logger.warning(f"⚠️ {service_name} operation failed: {error}")
        
        # Check if we should open the circuit breaker
        if (service_state["failure_count"] >= self.failure_threshold and 
            service_state["state"] != CircuitBreakerState.OPEN):
            
            service_state["state"] = CircuitBreakerState.OPEN
            logger.error(f"🚨 Circuit breaker for {service_name} OPENED after {service_state['failure_count']} failures")
    
    def get_state(self, service_name: Optional[str] = None) -> dict:
        """Get current circuit breaker state(s)"""
        if service_name:
            if service_name in self.service_states:
                return {
                    service_name: {
                        "state": self.service_states[service_name]["state"],
                        "failure_count": self.service_states[service_name]["failure_count"],
                        "success_count": self.service_states[service_name]["success_count"]
                    }
                }
            else:
                return {service_name: {"state": "NOT_INITIALIZED"}}
        else:
            # Return all service states
            states = {}
            for service, state in self.service_states.items():
                states[service] = {
                    "state": state["state"],
                    "failure_count": state["failure_count"],
                    "success_count": state["success_count"]
                }
            return states
    
    def reset_circuit_breaker(self, service_name: str):
        """Manually reset circuit breaker for a service"""
        if service_name in self.service_states:
            self.service_states[service_name] = {
                "state": CircuitBreakerState.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "last_failure_time": None
            }
            logger.info(f"🔄 Manually reset circuit breaker for {service_name}")
    
    def get_service_availability(self) -> dict:
        """Get availability status of all services"""
        availability = {}
        
        for service_name, state in self.service_states.items():
            if state["state"] == CircuitBreakerState.CLOSED:
                availability[service_name] = "available"
            elif state["state"] == CircuitBreakerState.HALF_OPEN:
                availability[service_name] = "testing"
            else:
                availability[service_name] = "unavailable"
        
        return availability