import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import settings
from src.auth.security import decode_token


pytestmark = pytest.mark.integration


async def _register_and_login(client, email: str) -> dict[str, str | int]:
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse"},
    )
    assert register.status_code == 201
    assert register.json()["email"] == email
    assert "id" in register.json()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-horse"},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["access_token"]
    assert body["refresh_token"]
    return body


def _auth(tokens: dict[str, str | int]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_register_login_refresh_logout_flow(api_client) -> None:
    """Refresh token rotation should revoke the previous refresh token."""
    tokens = await _register_and_login(api_client, "alice@example.com")

    refresh = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh.status_code == 200
    rotated = refresh.json()
    assert rotated["refresh_token"] != tokens["refresh_token"]

    old_refresh = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert old_refresh.status_code == 401
    assert old_refresh.json()["detail"] == "Invalid refresh token."

    logout = await api_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": rotated["refresh_token"]},
    )
    assert logout.status_code == 204
    after_logout = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated["refresh_token"]},
    )
    assert after_logout.status_code == 401
    assert after_logout.json()["detail"] == "Invalid refresh token."


def test_expired_access_token_is_rejected() -> None:
    """JWT expiration should be enforced during token decode."""
    expired = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(seconds=1),
            "iat": datetime.now(UTC) - timedelta(minutes=5),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(HTTPException):
        decode_token(expired, expected_type="access")


async def test_workspace_rbac_blocks_viewer_from_admin_action(api_client) -> None:
    """Workspace viewers can read but cannot mutate admin-only resources."""
    owner_tokens = await _register_and_login(api_client, "owner@example.com")
    viewer_tokens = await _register_and_login(api_client, "viewer@example.com")

    viewer_profile = jwt.decode(
        viewer_tokens["access_token"],
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    workspace_response = await api_client.post(
        "/api/v1/workspaces",
        json={"name": "Team"},
        headers=_auth(owner_tokens),
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    add_member = await api_client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        json={"user_id": viewer_profile["sub"], "role": "viewer"},
        headers=_auth(owner_tokens),
    )
    assert add_member.status_code == 201

    viewer_read = await api_client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers=_auth(viewer_tokens),
    )
    assert viewer_read.status_code == 200
    assert viewer_read.json()["name"] == "Team"

    viewer_update = await api_client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        json={"name": "Nope"},
        headers=_auth(viewer_tokens),
    )
    assert viewer_update.status_code == 403
    assert "permission" in viewer_update.json()["detail"].lower()
