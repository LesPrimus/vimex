from unittest import mock

import httpx
import pytest

import vimex
from vimex._data_structures import ServerFlowResult
from vimex._oauth2_server import MockedCallBackServer

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
STATE = "very_long_state"
API_ROOT = "https://some_website.com"


class TestAuthorizationCodeAuth:
    @mock.patch("vimex.VimeoOauth2AuthorizationCode.send_request")
    def test_code_flow_with_200(self, mocked_send_request):
        mocked_send_request.return_value = httpx.Response(
            200, json={"access_token": "some_access_token"}
        )

        auth = vimex.VimeoOauth2AuthorizationCode(
            CLIENT_ID, CLIENT_SECRET, state="long___state"
        )

        mocked_server = MockedCallBackServer()
        auth.server = mocked_server
        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        mocked_server.result.code = "some_code"
        request = next(flow)

        assert request.headers[auth.header_name] == auth.header_value.format(
            token="some_access_token"
        )

    @mock.patch("vimex.VimeoOauth2AuthorizationCode.send_request")
    def test_code_flow_without_code_in_response(self, mocked_send_request):
        auth = vimex.VimeoOauth2AuthorizationCode(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            state=STATE,
        )
        server = MockedCallBackServer()
        auth.server = server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        server.result = ServerFlowResult()

        request = next(flow)
        assert "Authorization" not in request.headers
        mocked_send_request.assert_not_called()

    @mock.patch("vimex.VimeoOauth2AuthorizationCode.send_request")
    def test_auth_flow_with_400_response(self, mocked_send_request):
        mocked_send_request.return_value = httpx.Response(400)
        auth = vimex.VimeoOauth2AuthorizationCode(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        mocked_server.result.code = "some_code"
        request = next(flow)
        assert "Authorization" not in request.headers

    @mock.patch("vimex.VimeoOauth2AuthorizationCode.send_request")
    def test_auth_flow_with_cached_access_token(self, mocked_send_request):
        auth = vimex.VimeoOauth2AuthorizationCode(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            state=STATE,
            access_token="some_cached_access_token",
        )

        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)
        request = next(flow)
        assert request.headers[auth.header_name] == auth.header_value.format(
            token=auth.access_token
        )
        mocked_send_request.assert_not_called()


@pytest.mark.anyio
class TestAsyncAuthorizationCodeAuth:
    @mock.patch("vimex.VimeoOauth2AuthorizationCode.async_send_request")
    async def test_code_flow_with_200(self, mocked_async_send_request):
        mocked_async_send_request.return_value = httpx.Response(
            200, json={"access_token": "some_access_token"}
        )

        auth = vimex.VimeoOauth2AuthorizationCode(
            CLIENT_ID, CLIENT_SECRET, state="long___state"
        )

        mocked_server = MockedCallBackServer()
        auth.server = mocked_server
        request = httpx.Request("GET", API_ROOT)
        flow = auth.async_auth_flow(request)
        # code from vimeo.
        mocked_server.result.code = "some_code"
        request = await anext(flow)
        assert request.headers[auth.header_name] == auth.header_value.format(
            token="some_access_token"
        )

    @mock.patch("vimex.VimeoOauth2AuthorizationCode.async_send_request")
    async def test_code_flow_with_400(self, mocked_async_send_request):
        mocked_async_send_request.return_value = None

        auth = vimex.VimeoOauth2AuthorizationCode(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            state=STATE,
        )
        server = MockedCallBackServer()
        auth.server = server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.async_auth_flow(request)

        # No code from Vimeo
        server.result = ServerFlowResult()

        request = await anext(flow)
        assert "Authorization" not in request.headers
        mocked_async_send_request.assert_not_called()

    @mock.patch("vimex.VimeoOauth2AuthorizationCode.async_send_request")
    async def test_auth_flow_with_400_response(self, mocked_async_request):
        mocked_async_request.return_value = httpx.Response(400)

        auth = vimex.VimeoOauth2AuthorizationCode(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.async_auth_flow(request)

        # code from vimeo
        mocked_server.result.code = "some_code"
        request = await anext(flow)

        assert "Authorization" not in request.headers
