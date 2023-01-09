import base64
from typing import Generator
import logging
import httpx
from httpx import Request
import webbrowser


from ._oauth2_server import Server

logger = logging.getLogger(__name__)


def _encode_client_credentials(client_id: str, client_secret: str) -> str:
    return base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()


class VimeoOAuth2ClientCredentials(httpx.Auth):
    requires_response_body = True
    access_token_url = "https://api.vimeo.com/oauth/authorize/client"
    header_name = "Authorization"
    header_value = "Bearer {token}"
    token_field_name = "access_token"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        # todo add cache..
        response = yield self.build_access_token_request()
        if response.is_success:
            token = response.json().get(self.token_field_name, None)
            request.headers[self.header_name] = self.header_value.format(token=token)
        yield request

    def build_access_token_request(self):
        r = Request(
            method="POST",
            url=self.access_token_url,
            headers=self.get_client_credentials_headers(),
            data=self.get_client_credentials_body(),
        )
        return r

    def get_client_credentials_headers(self):
        encoded = _encode_client_credentials(self.client_id, self.client_secret)
        headers = {
            "Authorization": f"basic {encoded}",
            "Accept": "application/vnd.vimeo.*+json;version=3.4",
        }
        return headers

    def get_client_credentials_body(self) -> dict:
        body = {"scope": "public", "grant_type": "client_credentials"}
        return body


class VimeoOauth2AuthorizationCode(httpx.Auth):
    requires_response_body = True
    authorization_url = "https://api.vimeo.com/oauth/authorize?" \
                "response_type=code" \
                "&client_id={client_id}" \
                "&redirect_uri={redirect_uri}" \
                "&state={state}" \
                "&scope={scope}"

    exchange_url = "https://api.vimeo.com/oauth/access_token"
    server_address = "http://127.0.0.1:5555"
    header_name = "Authorization"
    header_value = "Bearer {token}"
    token_field_name = "access_token"
    default_scope = "public private"

    def __init__(self, client_id, client_secret, state, scope=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.state = state
        self.redirect_uri = self.server_address
        self.scope = " ".join(scope) if scope and isinstance(scope, list) else self.default_scope

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        grant = self.get_authorization_code()
        # todo add cache..
        if grant and isinstance(grant, tuple) and len(grant) == 2:
            code, state = grant
            # todo check state.
            response = yield self.build_access_token_request(code)
            if response.is_success:
                token = response.json().get(self.token_field_name, None)
                # todo add check if token is not none..
                request.headers[self.header_name] = self.header_value.format(token=token)
        yield request

    def build_access_token_request(self, code):
        r = Request(
            method="POST",
            url=self.exchange_url,
            headers=self.get_client_credentials_headers(),
            data=self.get_client_credentials_body(code)
        )
        return r

    def get_authorization_code(self):
        with Server() as server:
            self.open_link()
            while not server.event.is_set():
                server.handle_request()
        return server.grant

    def format_token_url(self) -> str:
        return self.authorization_url.format(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            state=self.state,
            scope=self.scope,
        )

    def get_client_credentials_headers(self):
        encoded = _encode_client_credentials(self.client_id, self.client_secret)
        headers = {
            "Authorization": f"basic {encoded}",
            "Accept": "application/vnd.vimeo.*+json;version=3.4",
        }
        return headers

    def get_client_credentials_body(self, code) -> dict:
        body = {
            "grant_type": "authorization_code",
            "code": str(code),
            "redirect_uri": self.redirect_uri
        }
        return body

    def open_link(self):
        link = self.format_token_url()
        webbrowser.open(link)
