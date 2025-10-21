import logging
import time
from typing import Callable
from django.http import HttpRequest, HttpResponse


logger = logging.getLogger('django.request')


class RequestLoggingMiddleware:
    """
    Logs each request method, path, remote addr, response status and duration.
    Keeps payload/body out of logs by default to avoid PII leakage.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.time()
        response: HttpResponse
        try:
            response = self.get_response(request)
            return response
        finally:
            duration_ms = int((time.time() - start) * 1000)
            # Use info for success, warning/error for high latency
            level = logging.INFO
            if duration_ms > 3000:
                level = logging.WARNING
            if hasattr(response, 'status_code') and response.status_code >= 500:
                level = logging.ERROR

            logger.log(
                level,
                "method=%s path=%s status=%s duration_ms=%s ip=%s",
                request.method,
                request.get_full_path(),
                getattr(response, 'status_code', 'unknown'),
                duration_ms,
                request.META.get('REMOTE_ADDR', ''),
            )
