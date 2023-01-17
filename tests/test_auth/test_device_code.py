from unittest import mock

import httpx
import pytest

import vimex
from vimex._oauth2_server import MockedCallBackServer

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
API_ROOT = "https://some_website.com"
STATE = "VeryLongState"


class TestDeviceCodeAuth:
    @mock.patch("vimex._oauth2_server.MockedCallBackServer.poll_authorize_url")
    @mock.patch("vimex.VimeoOauth2DeviceCodeGrant.send_request")
    def test_device_flow_with_200(self, mocked_send_request, mocked_poll_authorize_url):
        json_response = vimex.DeviceCodeGrantResponse(
            device_code="some_device_code",
            user_code="some_user_code",
            authorize_link="https://some-authorize-link",
            activate_link="https://some-activate-link",
            expires_in=600,
            interval=10,
        )._asdict()

        mocked_send_request.return_value = httpx.Response(
            status_code=200, json=json_response
        )

        mocked_poll_authorize_url.return_value = httpx.Response(
            200, json={"access_token": "some_access_token"}
        )

        auth = vimex.VimeoOauth2DeviceCodeGrant(CLIENT_ID, CLIENT_SECRET, STATE)
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        request = next(flow)
        assert request.headers[auth.header_name] == auth.header_value.format(
            token="some_access_token"
        )

    @mock.patch("vimex._oauth2_server.MockedCallBackServer.poll_authorize_url")
    @mock.patch("vimex.VimeoOauth2DeviceCodeGrant.send_request")
    def test_device_flow_with_400(self, mocked_send_request, mocked_poll_authorize_url):
        mocked_send_request.return_value = httpx.Response(400)

        auth = vimex.VimeoOauth2DeviceCodeGrant(CLIENT_ID, CLIENT_SECRET, STATE)
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        request = next(flow)
        assert "Authorization" not in request.headers
        mocked_poll_authorize_url.assert_not_called()

    @mock.patch("vimex._oauth2_server.MockedCallBackServer.poll_authorize_url")
    @mock.patch("vimex.VimeoOauth2DeviceCodeGrant.send_request")
    def test_device_flow_with_400_from_polling_url(
        self, mocked_send_request, mocked_poll_authorize_url
    ):
        json_response = vimex.DeviceCodeGrantResponse(
            device_code="some_device_code",
            user_code="some_user_code",
            authorize_link="https://some-authorize-link",
            activate_link="https://some-activate-link",
            expires_in=600,
            interval=10,
        )._asdict()

        mocked_send_request.return_value = httpx.Response(
            status_code=200, json=json_response
        )

        mocked_poll_authorize_url.return_value = httpx.Response(400)
        auth = vimex.VimeoOauth2DeviceCodeGrant(CLIENT_ID, CLIENT_SECRET, STATE)
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        request = next(flow)

        assert "Authorization" not in request.headers


@pytest.mark.anyio
class TestAsyncDeviceCodeAuth:
    @mock.patch("vimex._oauth2_server.MockedCallBackServer.async_poll_authorize_url")
    @mock.patch("vimex.VimeoOauth2DeviceCodeGrant.async_send_request")
    async def test_device_flow_with_200(
        self, mocked_async_send_request, mocked_async_poll_authorize_url
    ):
        json_response = vimex.DeviceCodeGrantResponse(
            device_code="some_device_code",
            user_code="some_user_code",
            authorize_link="https://some-authorize-link",
            activate_link="https://some-activate-link",
            expires_in=600,
            interval=10,
        )._asdict()

        mocked_async_send_request.return_value = httpx.Response(
            status_code=200, json=json_response
        )

        mocked_async_poll_authorize_url.return_value = httpx.Response(
            200, json={"access_token": "some_access_token"}
        )

        auth = vimex.VimeoOauth2DeviceCodeGrant(CLIENT_ID, CLIENT_SECRET, STATE)
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.async_auth_flow(request)

        request = await anext(flow)
        assert request.headers[auth.header_name] == auth.header_value.format(
            token="some_access_token"
        )

    @mock.patch("vimex._oauth2_server.MockedCallBackServer.async_poll_authorize_url")
    @mock.patch("vimex.VimeoOauth2DeviceCodeGrant.async_send_request")
    async def test_device_flow_with_400(
        self, mocked_send_request, mocked_poll_authorize_url
    ):
        mocked_send_request.return_value = httpx.Response(400)

        auth = vimex.VimeoOauth2DeviceCodeGrant(CLIENT_ID, CLIENT_SECRET, STATE)
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.async_auth_flow(request)

        request = await anext(flow)
        assert "Authorization" not in request.headers
        mocked_poll_authorize_url.assert_not_called()

    @mock.patch("vimex._oauth2_server.MockedCallBackServer.poll_authorize_url")
    @mock.patch("vimex.VimeoOauth2DeviceCodeGrant.send_request")
    def test_device_flow_with_400_from_polling_url(
        self, mocked_send_request, mocked_poll_authorize_url
    ):
        json_response = vimex.DeviceCodeGrantResponse(
            device_code="some_device_code",
            user_code="some_user_code",
            authorize_link="https://some-authorize-link",
            activate_link="https://some-activate-link",
            expires_in=600,
            interval=10,
        )._asdict()

        mocked_send_request.return_value = httpx.Response(
            status_code=200, json=json_response
        )

        mocked_poll_authorize_url.return_value = httpx.Response(400)
        auth = vimex.VimeoOauth2DeviceCodeGrant(CLIENT_ID, CLIENT_SECRET, STATE)
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        request = next(flow)

        assert "Authorization" not in request.headers
