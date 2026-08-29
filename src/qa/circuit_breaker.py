import logging

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, max_failures: int = 1):
        self.max_failures = max_failures
        self.failure_count = 0
        self.is_tripped = False

    def record_failure(self, reason: str = ""):
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            self.is_tripped = True
            logger.warning(f"Circuit Breaker TRIPPED due to LLM failure: {reason}. Skipping LLM calls for rest of run.")

    def record_success(self):
        # Successful call
        pass

    def can_execute(self) -> bool:
        return not self.is_tripped

    def reset(self):
        self.failure_count = 0
        self.is_tripped = False

# Global single-run instance
circuit_breaker = CircuitBreaker()
