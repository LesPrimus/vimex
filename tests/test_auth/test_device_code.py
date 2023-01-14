from unittest import mock

import httpx

import vimex
from vimex._oauth2_server import MockedCallBackServer

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
API_ROOT = "https://some_website.com"
STATE = "VeryLongState"


class TestDeviceCodeAuth:
    def test_device_flow_with_200(self):
        auth = vimex.VimeoOauth2DeviceCodeGrant(CLIENT_ID, CLIENT_SECRET, STATE)
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

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

        with mock.patch(
            "vimex._oauth2_server.MockedCallBackServer.poll_authorize_url"
        ) as mocked_method:
            mocked_method.return_value = httpx.Response(
                200, json={"access_token": "some_access_token"}
            )
            request = flow.send(response)
            assert request.headers["Authorization"] == f"Bearer some_access_token"

    def test_device_flow_with_400(self):
        auth = vimex.VimeoOauth2DeviceCodeGrant(CLIENT_ID, CLIENT_SECRET, STATE)
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

        request = next(flow)

        assert request.headers["Authorization"].startswith("basic")

        response = httpx.Response(status_code=400, json={})

        request = flow.send(response)
        assert "Authorization" not in request.headers

    def test_device_flow_with_400_from_polling_url(self):
        auth = vimex.VimeoOauth2DeviceCodeGrant(CLIENT_ID, CLIENT_SECRET, STATE)
        mocked_server = MockedCallBackServer()
        auth.server = mocked_server

        request = httpx.Request("GET", API_ROOT)

        flow = auth.sync_auth_flow(request)

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

        with mock.patch(
            "vimex._oauth2_server.MockedCallBackServer.poll_authorize_url"
        ) as mocked_method:
            mocked_method.return_value = httpx.Response(400, json={})
            request = flow.send(response)
            assert "Authorization" not in request.headers
