#!/usr/bin/env python3
"""通用重试工具 — 指数退避重试装饰器 + HTTP 错误分类。

符合 api-usage.md 规范：max 3 次重试，间隔 1s → 3s → 10s。
"""

import time
import logging
import functools
import requests

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class RetryableError(Exception):
    """可重试的瞬时错误（网络超时、限流、5xx）"""
    pass


class NonRetryableError(Exception):
    """不可重试的永久错误（4xx 认证/参数错误）"""
    pass


def with_retry(max_retries=3, delays=(1, 3, 10), retryable_exceptions=(RetryableError, ConnectionError, TimeoutError, requests.ConnectionError, requests.Timeout)):
    """指数退避重试装饰器。"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except NonRetryableError:
                    raise
                except retryable_exceptions as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = delays[min(attempt, len(delays) - 1)]
                        logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {str(e)[:100]}. Waiting {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} retries exhausted for {func.__name__}: {str(e)[:100]}")
                except Exception:
                    raise
            raise last_error
        return wrapper
    return decorator


def check_response(resp: requests.Response) -> requests.Response:
    """检查 HTTP 响应，将错误分类为可重试/不可重试。"""
    if resp.ok:
        return resp
    error_body = resp.text[:300] if resp.text else ""
    if resp.status_code in RETRYABLE_STATUS_CODES:
        raise RetryableError(f"HTTP {resp.status_code}: {error_body}")
    elif 400 <= resp.status_code < 500:
        raise NonRetryableError(f"HTTP {resp.status_code}: {error_body}")
    else:
        raise RetryableError(f"HTTP {resp.status_code}: {error_body}")
