import httpx

import vimex

CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
API_ROOT = "https://some_website.com"


class TestClientCredentialsAuth:
    def test_auth_flow_set_header_with_200(self):
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        request = httpx.Request("GET", API_ROOT)

        flow = auth.auth_flow(request)

        request = next(flow)
        assert request.headers["Authorization"].startswith("basic")

        json_response = {
            "access_token": "some_access_token",
            "token_type": "bearer",
            "scope": "foo, bar"
        }

        response = httpx.Response(status_code=200, json=json_response)
        request = flow.send(response)
        assert request.headers['Authorization'] == f"Bearer {json_response['access_token']}"

    def test_auth_flow_set_header_with_400(self):
        auth = vimex.VimeoOAuth2ClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        request = httpx.Request("GET", API_ROOT)

        flow = auth.auth_flow(request)

        request = next(flow)
        assert request.headers["Authorization"].startswith("basic")

        response = httpx.Response(status_code=400)
        request = flow.send(response)

        assert "Authorization" not in request.headers
