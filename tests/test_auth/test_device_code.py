import pytest

from unittest import mock
import httpx

import vimex

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
API_ROOT = "https://some_website.com"


class TestDeviceCodeAuth:
    @mock.patch("vimex._auth.VimeoOauth2DeviceCodeGrant.poll_authorize_url")
    def test_auth_flow_with_grant_set_header(self, mock_poll_authorize_url):
        mock_poll_authorize_url.return_value = httpx.Response(
            status_code=200,
            json={
                "access_token": "some_access_token",
                "token_type": "bearer",
                "scope": "some scope",
                "user": "some_user_data",
            },
        )

        auth = vimex.VimeoOauth2DeviceCodeGrant(
            CLIENT_ID, CLIENT_SECRET, state="long___state"
        )
        request = httpx.Request("GET", API_ROOT)

        flow = auth.auth_flow(request)

        request = next(flow)

        assert request.headers["Authorization"].startswith("basic")

        json_response = vimex.DeviceCodeGrantResponse(
            device_code="some_device_code",
            user_code="some_user_code",
            authorize_link="https://some-authorize-link",
            activate_link="https://some-activate-link",
            expires_in=600,
            interval=10,
        )._asdict()

        response = httpx.Response(status_code=200, json=json_response)

        request = flow.send(response)

        assert request.headers["Authorization"] == f"Bearer some_access_token"
