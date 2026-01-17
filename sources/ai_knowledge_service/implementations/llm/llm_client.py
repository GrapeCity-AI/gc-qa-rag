"""
LLM Client - OpenAI-compatible client with rate limiting.

Provides a thread-safe client for calling OpenAI-compatible LLM APIs
with built-in rate limiting to prevent exceeding API quotas.
"""

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from openai import OpenAI


@dataclass
class LLMConfig:
    """Configuration for LLM client."""

    api_key: str
    api_base: str
    model_name: str = "qwen-plus"
    max_rpm: int = 60  # Max requests per minute
    temperature: float = 0.7
    top_p: float = 0.7
    system_prompt: str = "你是一个乐于解答各种问题的助手。"
    timeout: float = 60.0  # Request timeout in seconds


class RateLimiter:
    """
    Thread-safe rate limiter with RPM (requests per minute) support.

    Uses a sliding window approach to track requests within the time window.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed within the time window.
            window_seconds: Time window size in seconds (default: 60 seconds).
        """
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: Deque[float] = deque()
        self._lock = threading.Lock()

    @property
    def max_requests(self) -> int:
        """Get maximum requests per window."""
        return self._max_requests

    @property
    def window_seconds(self) -> int:
        """Get window size in seconds."""
        return self._window_seconds

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Try to acquire request permission.

        Args:
            timeout: Timeout in seconds. None means wait indefinitely.

        Returns:
            bool: True if permission was acquired.
        """
        start_time = time.time()

        while True:
            with self._lock:
                current_time = time.time()

                # Clean up expired request records
                while self._requests and current_time - self._requests[0] > self._window_seconds:
                    self._requests.popleft()

                # Check if request can be sent
                if len(self._requests) < self._max_requests:
                    self._requests.append(current_time)
                    return True

            # Check timeout
            if timeout is not None and time.time() - start_time >= timeout:
                return False

            # Wait before retrying
            time.sleep(0.1)

    def wait_and_acquire(self) -> None:
        """Wait until request permission can be acquired (blocking)."""
        self.acquire(timeout=None)

    def get_remaining_requests(self) -> int:
        """Get remaining requests in current time window."""
        with self._lock:
            current_time = time.time()

            # Clean up expired request records
            while self._requests and current_time - self._requests[0] > self._window_seconds:
                self._requests.popleft()

            return max(0, self._max_requests - len(self._requests))

    def get_reset_time(self) -> Optional[float]:
        """
        Get timestamp when next request can be sent.

        Returns:
            Timestamp when next request can be sent, or None if available now.
        """
        with self._lock:
            current_time = time.time()

            # Clean up expired request records
            while self._requests and current_time - self._requests[0] > self._window_seconds:
                self._requests.popleft()

            if len(self._requests) < self._max_requests:
                return None

            # Return the expiration time of the earliest request
            return self._requests[0] + self._window_seconds


class LLMClient:
    """
    OpenAI-compatible LLM client with rate limiting.

    Thread-safe implementation that supports rate limiting to prevent
    exceeding API quotas. Uses the OpenAI client library for API calls.
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize LLM client.

        Args:
            config: LLM configuration.
        """
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
            timeout=config.timeout,
        )
        self._rate_limiter = RateLimiter(
            max_requests=config.max_rpm,
            window_seconds=60,
        )
        self._lock = threading.RLock()

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._config.model_name

    def _create_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Create a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Returns:
            str: The completion response content.

        Raises:
            Exception: If the API call fails.
        """
        # Apply rate limiting before sending request
        self._rate_limiter.wait_and_acquire()

        completion = self._client.chat.completions.create(
            model=self._config.model_name,
            messages=messages,
            top_p=self._config.top_p,
            temperature=self._config.temperature,
        )

        return completion.choices[0].message.content or ""

    def chat(self, content: str) -> str:
        """
        Send a single message to the LLM.

        Args:
            content: The user message content.

        Returns:
            str: The LLM response.
        """
        messages = [
            {"role": "system", "content": self._config.system_prompt},
            {"role": "user", "content": content},
        ]
        return self._create_completion(messages)

    def chat_with_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Send a conversation to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Returns:
            str: The LLM response.
        """
        return self._create_completion(messages)

    def chat_with_system(self, system_prompt: str, content: str) -> str:
        """
        Send a message with a custom system prompt.

        Args:
            system_prompt: Custom system prompt.
            content: The user message content.

        Returns:
            str: The LLM response.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]
        return self._create_completion(messages)

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Dict containing remaining requests and reset time info.
        """
        remaining = self._rate_limiter.get_remaining_requests()
        reset_time = self._rate_limiter.get_reset_time()

        return {
            "remaining_requests": remaining,
            "reset_time": reset_time,
            "max_rpm": self._rate_limiter.max_requests,
            "window_seconds": self._rate_limiter.window_seconds,
        }
