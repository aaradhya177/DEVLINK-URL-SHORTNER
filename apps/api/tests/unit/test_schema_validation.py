import pytest
from pydantic import ValidationError

from src.auth.schemas import RegisterRequest
from src.links.schemas import BulkLinkCreateRequest, LinkCreate
from src.redirect.schemas import PasswordVerifyRequest


def test_request_models_reject_unexpected_fields() -> None:
    """API request models should not silently ignore client-supplied fields."""
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="user@example.com",
            password="correct-horse",
            is_admin=True,
        )
    with pytest.raises(ValidationError):
        LinkCreate(
            destination_url="https://example.com",
            owner_id="00000000-0000-0000-0000-000000000000",
        )
    with pytest.raises(ValidationError):
        PasswordVerifyRequest(password="secret", redirect_token="fake")


def test_bulk_link_request_validates_each_url() -> None:
    """Bulk shortening should reject one unsafe URL before service processing."""
    with pytest.raises(ValidationError):
        BulkLinkCreateRequest(
            urls=["https://example.com", "http://127.0.0.1/admin"],
        )
