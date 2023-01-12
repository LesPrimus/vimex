import httpx
import pytest

import vimex


CLIENT_ID = "some_long_id"
CLIENT_SECRET = "some_very_secret"
API_ROOT = "https://some_website.com"


class App:
    def __init__(self, auth_header: str = "", status_code: int = 200) -> None:
        self.auth_header = auth_header
        self.status_code = status_code

    def __call__(self, request: httpx.Request) -> httpx.Response:
        headers = {"www-authenticate": self.auth_header} if self.auth_header else {}
        data = {"auth": request.headers.get("Authorization")}
        return httpx.Response(self.status_code, headers=headers, json=data)


@pytest.mark.anyio
async def test_client_credentials_grant_async_client():
    app = App()

    auth = vimex.VimeoOAuth2ClientCredentials(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET
    )

    async with vimex.AsyncVimeoClient(
        transport=httpx.MockTransport(app), auth=auth
    ) as client:
        response = await client.get(API_ROOT)

    assert response.status_code == 200
    assert response.json()["auth"].startswith("Bearer")


def test_client_credentials_grant_sync_client():
    app = App()

    auth = vimex.VimeoOAuth2ClientCredentials(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET
    )

    with vimex.VimeoClient(transport=httpx.MockTransport(app), auth=auth) as client:
        response = client.get(API_ROOT)

    assert response.status_code == 200
    assert response.json()["auth"].startswith("Bearer")


# @pytest.mark.anyio
# async def test_authorization_code_grant_async_client():
#     app = App()
#
#     auth = vimex.VimeoOauth2AuthorizationCode(
#         client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state="some_very_long_state"
#     )
#
#     async with vimex.AsyncVimeoClient(
#         transport=httpx.MockTransport(app), auth=auth
#     ) as client:
#         response = await client.get(API_ROOT)
#
#     assert response.status_code == 200
#     assert response.json()["auth"].startswith("Bearer")


# def test_authorization_code_grant_sync_client():
#     app = App()
#
#     auth = vimex.VimeoOauth2AuthorizationCode(
#         client_id=CLIENT_ID, client_secret=CLIENT_SECRET, state="some_very_long_state"
#     )
#
#     with vimex.VimeoClient(transport=httpx.MockTransport(app), auth=auth) as client:
#         response = client.get(API_ROOT)
#
#     print(response)
#     assert 0
