from unittest import mock

import httpx

import vimex

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
API_ROOT = "https://some_website.com"


class TestImplicitGrantAuth:
    @mock.patch("vimex._auth.VimeoOauth2ImplicitGrant.get_authorization_grant")
    def test_auth_flow_set_header_with_200(self, mocked_get_authorization_grant):
        access_token = "some_access_token"
        mocked_get_authorization_grant.return_value = (access_token, "SomeVeryLongState")
        auth = vimex.VimeoOauth2ImplicitGrant(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            state="long___state"
        )
        request = httpx.Request("GET", API_ROOT)

        flow = auth.auth_flow(request)

        mocked_get_authorization_grant.assert_not_called()
        request = next(flow)
        mocked_get_authorization_grant.assert_called_once()

        assert request.headers["Authorization"] == f"Bearer {access_token}"

    @mock.patch("vimex._auth.VimeoOauth2ImplicitGrant.get_authorization_grant")
    def test_auth_flow_dont_set_header_with_4xx(self, mocked_get_authorization_grant):
        mocked_get_authorization_grant.return_value = None
        auth = vimex.VimeoOauth2ImplicitGrant(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            state="long___state"
        )
        request = httpx.Request("GET", API_ROOT)

        flow = auth.auth_flow(request)

        request = next(flow)
        assert "Authorization" not in request.headers
