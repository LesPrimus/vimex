from unittest import mock
import httpx

import vimex
from vimex._oauth2_server import MockedCallBackServer

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
API_ROOT = "https://some_website.com"


class TestAuthorizationCodeAuth:
    def test_auth_flow_with_grant_set_header(self):
        auth = vimex.VimeoOauth2AuthorizationCode(
            CLIENT_ID,
            CLIENT_SECRET,
            state="long___state",
            server=MockedCallBackServer(code="some_code", state="long__state"),
        )

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        request = next(flow)

        assert request.headers["Authorization"].startswith("basic")

        json_response = {
            "access_token": "brand_new_token",
            "token_type": "bearer",
            "scope": "foo, bar",
            "user": "some_user_representation"
        }

        response = httpx.Response(status_code=200, json=json_response)
        request = flow.send(response)
        assert request.headers['Authorization'] == f"Bearer {json_response['access_token']}"

    def test_auth_flow_without_grant(self):
        auth = vimex.VimeoOauth2AuthorizationCode(
            CLIENT_ID,
            CLIENT_SECRET,
            state="long___state",
            server=MockedCallBackServer(code=None, state=None),
        )

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        request = next(flow)
        assert "Authorization" not in request.headers

    def test_auth_flow_with_401_response(self):

        auth = vimex.VimeoOauth2AuthorizationCode(
            CLIENT_ID,
            CLIENT_SECRET,
            state="long___state",
            server=MockedCallBackServer(code="some_code", state="some_state"),
        )
        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        request = next(flow)
        assert request.headers["Authorization"].startswith("basic")

        response = httpx.Response(status_code=401)
        request = flow.send(response)
        assert 'Authorization' not in request.headers

# todo add test for async_auth_flow.
