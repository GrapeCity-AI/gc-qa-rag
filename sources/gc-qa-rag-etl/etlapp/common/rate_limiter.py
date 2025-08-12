import threading
import time
from collections import deque
from typing import Optional


class RateLimiter:
    """
    线程安全的速率限制器，支持RPM（每分钟请求数）限制
    """
    
    def __init__(self, max_requests: int, window_seconds: int = 60):
        """
        初始化速率限制器
        
        Args:
            max_requests: 在指定时间窗口内允许的最大请求数
            window_seconds: 时间窗口大小（秒），默认60秒（1分钟）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = threading.Lock()
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        尝试获取请求许可
        
        Args:
            timeout: 超时时间（秒），None表示无限等待
            
        Returns:
            bool: 是否成功获取许可
        """
        start_time = time.time()
        
        while True:
            with self._lock:
                current_time = time.time()
                
                # 清理过期的请求记录
                while self.requests and current_time - self.requests[0] > self.window_seconds:
                    self.requests.popleft()
                
                # 检查是否可以发送请求
                if len(self.requests) < self.max_requests:
                    self.requests.append(current_time)
                    return True
            
            # 检查超时
            if timeout is not None and time.time() - start_time >= timeout:
                return False
            
            # 等待一小段时间再重试
            time.sleep(0.1)
    
    def wait_and_acquire(self) -> None:
        """
        等待直到可以获取请求许可（阻塞式）
        """
        self.acquire(timeout=None)
    
    def get_remaining_requests(self) -> int:
        """
        获取当前时间窗口内剩余的请求数
        
        Returns:
            int: 剩余请求数
        """
        with self._lock:
            current_time = time.time()
            
            # 清理过期的请求记录
            while self.requests and current_time - self.requests[0] > self.window_seconds:
                self.requests.popleft()
            
            return max(0, self.max_requests - len(self.requests))
    
    def get_reset_time(self) -> Optional[float]:
        """
        获取下次可以发送请求的时间戳
        
        Returns:
            Optional[float]: 下次可发送请求的时间戳，None表示立即可发送
        """
        with self._lock:
            current_time = time.time()
            
            # 清理过期的请求记录
            while self.requests and current_time - self.requests[0] > self.window_seconds:
                self.requests.popleft()
            
            if len(self.requests) < self.max_requests:
                return None
            
            # 返回最早请求过期的时间
            return self.requests[0] + self.window_seconds
