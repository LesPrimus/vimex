import httpx
import pytest

import vimex

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
STATE = "vERYlONGsTate"
API_ROOT = "https://some_website.com"


class TestClientCredentialsAuth:
    def test_client_credentials_flow_with_200(self):
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        request = httpx.Request("GET", API_ROOT)
        flow = auth.sync_auth_flow(request)
        request = next(flow)
        assert request.headers["Authorization"].startswith("basic")
        json_response = {
            "access_token": "some_access_token",
            "token_type": "bearer",
            "scope": STATE,
        }
        response = httpx.Response(status_code=200, json=json_response)
        request = flow.send(response)
        assert request.headers[auth.header_name] == auth.header_value.format(
            token=json_response[auth.token_field_name]
        )

    def test_client_credentials_flow_with_400(self):
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        request = httpx.Request("GET", API_ROOT)
        flow = auth.sync_auth_flow(request)
        request = next(flow)
        assert request.headers["Authorization"].startswith("basic")
        response = httpx.Response(status_code=400)
        request = flow.send(response)
        assert "Authorization" not in request.headers


@pytest.mark.anyio
class TestAsyncClientCredentialsAuth:
    async def test_async_client_credentials_flow_with_200(self):
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        request = httpx.Request("GET", API_ROOT)
        flow = auth.async_auth_flow(request)
        request = await anext(flow)
        assert request.headers["Authorization"].startswith("basic")
        json_response = {
            "access_token": "some_access_token",
            "token_type": "bearer",
            "scope": STATE,
        }
        response = httpx.Response(status_code=200, json=json_response)
        request = await flow.asend(response)
        assert request.headers[auth.header_name] == auth.header_value.format(
            token=json_response[auth.token_field_name]
        )

    async def test_client_credentials_flow_with_400(self):
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        request = httpx.Request("GET", API_ROOT)
        flow = auth.async_auth_flow(request)
        request = await anext(flow)
        assert request.headers["Authorization"].startswith("basic")
        response = httpx.Response(status_code=400)
        request = await flow.asend(response)
        assert "Authorization" not in request.headers
