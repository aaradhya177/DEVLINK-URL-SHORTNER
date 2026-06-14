import uuid

from fastapi import Request, Response

from src.shared.logging_utils import correlation_id_var


CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"


def get_request_correlation_id(request: Request) -> str:
    """Return the current request correlation ID."""
    value = getattr(request.state, "correlation_id", None)
    return str(value) if value else ""


async def correlation_id_middleware(request: Request, call_next) -> Response:
    """Attach or create a correlation ID for request logs and downstream events."""
    correlation_id = (
        request.headers.get(CORRELATION_ID_HEADER)
        or request.headers.get(REQUEST_ID_HEADER)
        or str(uuid.uuid4())
    )
    request.state.correlation_id = correlation_id
    token = correlation_id_var.set(correlation_id)
    try:
        response: Response = await call_next(request)
    finally:
        correlation_id_var.reset(token)
    response.headers[CORRELATION_ID_HEADER] = correlation_id
    response.headers[REQUEST_ID_HEADER] = correlation_id
    return response
