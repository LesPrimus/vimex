import httpx
import pytest

import vimex
from vimex._oauth2_server import MockedCallBackServer

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
API_ROOT = "https://some_website.com"
STATE = "VeryLongState"


class TestImplicitGrantAuth:
    def test_implicit_flow_with_access_token(self):
        auth = vimex.VimeoOauth2ImplicitGrant(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)
        flow = auth.sync_auth_flow(request)

        mocked_server.result.access_token = "Some_access_token"
        request = next(flow)

        assert request.headers[auth.header_name] == auth.header_value.format(
            token=mocked_server.result.access_token
        )

    def test_implicit_flow_without_access_token(self):
        auth = vimex.VimeoOauth2ImplicitGrant(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)
        flow = auth.sync_auth_flow(request)

        request = next(flow)

        assert "Authorization" not in request.headers

    def test_implicit_flow_with_cached_access_token(self):
        auth = vimex.VimeoOauth2ImplicitGrant(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            state=STATE,
            access_token="cached_access_token",
        )
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)
        flow = auth.sync_auth_flow(request)

        request = next(flow)

        assert request.headers[auth.header_name] == auth.header_value.format(
            token=auth.access_token
        )


@pytest.mark.anyio
class TestAsyncImplicitGrantAuth:
    async def test_implicit_flow_with_200(self):
        auth = vimex.VimeoOauth2ImplicitGrant(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)
        flow = auth.async_auth_flow(request)

        mocked_server.result.access_token = "Some_access_token"
        request = await anext(flow)

        assert request.headers[auth.header_name] == auth.header_value.format(
            token=mocked_server.result.access_token
        )

    async def test_implicit_flow_with_400(self):
        auth = vimex.VimeoOauth2ImplicitGrant(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)
        flow = auth.async_auth_flow(request)

        request = await anext(flow)

        assert "Authorization" not in request.headers

    async def test_implicit_flow_with_cached_access_token(self):
        auth = vimex.VimeoOauth2ImplicitGrant(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            state=STATE,
            access_token="some_cached_access_token",
        )
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)
        flow = auth.async_auth_flow(request)

        request = await anext(flow)

        assert request.headers[auth.header_name] == auth.header_value.format(
            token=auth.access_token
        )
