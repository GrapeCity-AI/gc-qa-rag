import threading
import time
from collections import deque
from typing import Optional


class RateLimiter:
    """
    Thread-safe rate limiter with RPM (requests per minute) support
    """
    
    def __init__(self, max_requests: int, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed within the specified time window
            window_seconds: Time window size in seconds, default is 60 seconds (1 minute)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = threading.Lock()
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Try to acquire request permission
        
        Args:
            timeout: Timeout in seconds, None means infinite wait
            
        Returns:
            bool: Whether permission was successfully acquired
        """
        start_time = time.time()
        
        while True:
            with self._lock:
                current_time = time.time()
                
                # Clean up expired request records
                while self.requests and current_time - self.requests[0] > self.window_seconds:
                    self.requests.popleft()
                
                # Check if request can be sent
                if len(self.requests) < self.max_requests:
                    self.requests.append(current_time)
                    return True
            
            # Check timeout
            if timeout is not None and time.time() - start_time >= timeout:
                return False
            
            # Wait a short time before retrying
            time.sleep(0.1)
    
    def wait_and_acquire(self) -> None:
        """
        Wait until request permission can be acquired (blocking)
        """
        self.acquire(timeout=None)
    
    def get_remaining_requests(self) -> int:
        """
        Get remaining requests in current time window
        
        Returns:
            int: Number of remaining requests
        """
        with self._lock:
            current_time = time.time()
            
            # Clean up expired request records
            while self.requests and current_time - self.requests[0] > self.window_seconds:
                self.requests.popleft()
            
            return max(0, self.max_requests - len(self.requests))
    
    def get_reset_time(self) -> Optional[float]:
        """
        Get timestamp when next request can be sent
        
        Returns:
            Optional[float]: Timestamp when next request can be sent, None means can send immediately
        """
        with self._lock:
            current_time = time.time()
            
            # Clean up expired request records
            while self.requests and current_time - self.requests[0] > self.window_seconds:
                self.requests.popleft()
            
            if len(self.requests) < self.max_requests:
                return None
            
            # Return the expiration time of the earliest request
            return self.requests[0] + self.window_seconds
