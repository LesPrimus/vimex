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
    def test_code_flow_with_200(self):
        auth = vimex.VimeoOauth2AuthorizationCode(
            CLIENT_ID, CLIENT_SECRET, state="long___state"
        )

        mocked_server = MockedCallBackServer()
        auth.server = mocked_server
        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        mocked_server.result.code = "some_code"
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

    def test_code_flow_with_400(self):
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

    def test_auth_flow_with_401_response(self):
        auth = vimex.VimeoOauth2AuthorizationCode(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        mocked_server.result.code = "some_code"
        request = next(flow)
        assert request.headers["Authorization"].startswith("basic")

        response = httpx.Response(status_code=401)
        request = flow.send(response)
        assert 'Authorization' not in request.headers


@pytest.mark.anyio
class TestAsyncAuthorizationCodeAuth:
    async def test_code_flow_with_200(self):
        auth = vimex.VimeoOauth2AuthorizationCode(
            CLIENT_ID, CLIENT_SECRET, state="long___state"
        )

        mocked_server = MockedCallBackServer()
        auth.server = mocked_server
        request = httpx.Request("GET", API_ROOT)
        flow = auth.async_auth_flow(request)
        mocked_server.result.code = "some_code"
        request = await anext(flow)

        assert request.headers["Authorization"].startswith("basic")

        json_response = {
            "access_token": "brand_new_token",
            "token_type": "bearer",
            "scope": "foo, bar",
            "user": "some_user_representation",
        }

        response = httpx.Response(status_code=200, json=json_response)
        request = await flow.asend(response)
        assert (
            request.headers["Authorization"]
            == f"Bearer {json_response['access_token']}"
        )

    async def test_code_flow_with_400(self):
        auth = vimex.VimeoOauth2AuthorizationCode(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            state=STATE,
        )
        server = MockedCallBackServer()
        auth.server = server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.async_auth_flow(request)

        server.result = ServerFlowResult()

        request = await anext(flow)
        assert "Authorization" not in request.headers

    async def test_auth_flow_with_401_response(self):
        auth = vimex.VimeoOauth2AuthorizationCode(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state=STATE
        )
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.async_auth_flow(request)

        mocked_server.result.code = "some_code"
        request = await anext(flow)
        assert request.headers["Authorization"].startswith("basic")

        response = httpx.Response(status_code=401)
        request = await flow.asend(response)
        assert "Authorization" not in request.headers
