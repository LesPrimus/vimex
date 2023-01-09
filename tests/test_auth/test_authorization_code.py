from unittest import mock
import httpx

import vimex

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
API_ROOT = "https://some_website.com"


class TestAuthorizationCodeAuth:
    @mock.patch("vimex._auth.VimeoOauth2AuthorizationCode.get_authorization_grant")
    def test_auth_flow_with_grant_set_header(self, mocked_get_authorization_code):
        mocked_get_authorization_code.return_value = ("auth_code", "SomeVeryLongState")

        auth = vimex.VimeoOauth2AuthorizationCode(CLIENT_ID, CLIENT_SECRET, state="long___state")
        request = httpx.Request("GET", API_ROOT)

        flow = auth.auth_flow(request)

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

    @mock.patch("vimex._auth.VimeoOauth2AuthorizationCode.get_authorization_grant")
    def test_auth_flow_without_grant(self, mocked_get_authorization_code):
        mocked_get_authorization_code.return_value = None

        auth = vimex.VimeoOauth2AuthorizationCode(CLIENT_ID, CLIENT_SECRET, state="long___state")
        request = httpx.Request("GET", API_ROOT)

        flow = auth.auth_flow(request)

        request = next(flow)
        assert "Authorization" not in request.headers

    @mock.patch("vimex._auth.VimeoOauth2AuthorizationCode.get_authorization_grant")
    def test_auth_flow_with_401_response(self, mocked_get_authorization_code):
        mocked_get_authorization_code.return_value = ("auth_code", "SomeVeryLongState")

        auth = vimex.VimeoOauth2AuthorizationCode(CLIENT_ID, CLIENT_SECRET, state="long___state")
        request = httpx.Request("GET", API_ROOT)

        flow = auth.auth_flow(request)

        request = next(flow)
        assert request.headers["Authorization"].startswith("basic")

        response = httpx.Response(status_code=401)
        request = flow.send(response)
        assert 'Authorization' not in request.headers
