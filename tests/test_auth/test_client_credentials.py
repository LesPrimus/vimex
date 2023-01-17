from unittest import mock

import httpx
import pytest

import vimex

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
STATE = "vERYlONGsTate"
API_ROOT = "https://some_website.com"


class TestClientCredentialsAuth:
    @mock.patch("vimex.VimeoOAuth2ClientCredentials.send_request")
    def test_client_credentials_flow_with_200(self, mocked_send_request):
        mocked_send_request.return_value = httpx.Response(
            200, json={"access_token": "some_access_token"}
        )
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )

        request = httpx.Request("GET", API_ROOT)
        flow = auth.sync_auth_flow(request)

        request = next(flow)

        assert request.headers[auth.header_name] == auth.header_value.format(
            token="some_access_token"
        )

    @mock.patch("vimex.VimeoOAuth2ClientCredentials.send_request")
    def test_client_credentials_flow_with_400(self, mocked_send_request):
        mocked_send_request.return_value = httpx.Response(400)
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        request = httpx.Request("GET", API_ROOT)
        flow = auth.sync_auth_flow(request)
        request = next(flow)
        assert "Authorization" not in request.headers

    @mock.patch("vimex.VimeoOAuth2ClientCredentials.send_request")
    def test_client_credentials_flow_with_cached_access_token(
        self, mocked_send_request
    ):
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            state=STATE,
            access_token="some_cached_acccess_token",
        )
        request = httpx.Request("GET", API_ROOT)
        flow = auth.sync_auth_flow(request)
        request = next(flow)
        assert request.headers["Authorization"] == auth.header_value.format(
            token=auth.access_token
        )
        mocked_send_request.assert_not_called()


@pytest.mark.anyio
class TestAsyncClientCredentialsAuth:
    @mock.patch("vimex.VimeoOAuth2ClientCredentials.async_send_request")
    async def test_async_client_credentials_flow_with_200(
        self, mocked_async_send_request
    ):
        mocked_async_send_request.return_value = httpx.Response(
            200, json={"access_token": "some_access_token"}
        )
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )

        request = httpx.Request("GET", API_ROOT)
        flow = auth.async_auth_flow(request)
        request = await anext(flow)
        assert request.headers[auth.header_name] == auth.header_value.format(
            token="some_access_token"
        )

    @mock.patch("vimex.VimeoOAuth2ClientCredentials.async_send_request")
    async def test_client_credentials_flow_with_400(self, mocked_async_send_request):
        mocked_async_send_request.return_value = httpx.Response(400)
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        request = httpx.Request("GET", API_ROOT)
        flow = auth.async_auth_flow(request)
        request = await anext(flow)
        assert "Authorization" not in request.headers

    @mock.patch("vimex.VimeoOAuth2ClientCredentials.async_send_request")
    async def test_client_credentials_flow_with_cached_access_token(
        self, mocked_async_send_request
    ):
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            state=STATE,
            access_token="1234:abcd",
        )
        request = httpx.Request("GET", API_ROOT)
        flow = auth.async_auth_flow(request)
        request = await anext(flow)
        assert request.headers["Authorization"] == auth.header_value.format(
            token=auth.access_token
        )
        mocked_async_send_request.assert_not_called()
