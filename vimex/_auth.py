import asyncio
import base64
import sys
import time
import typing
from typing import Generator, Optional
import logging
import httpx
import uvicorn
from httpx import Request, Response
import webbrowser

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from ._oauth2_server import Server, ServerFlow
from ._data_structures import DeviceCodeGrantResponse

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
    requires_request_body = True
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

    def __init__(self, client_id, client_secret, state, scope=None, server=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.state = state
        self.redirect_uri = self.server_address
        self.scope = " ".join(scope) if scope and isinstance(scope, list) else self.default_scope

        self.server = server or Server(redirect_on_fragment=False)

    def sync_auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        result = self.server.get_authorization_grant(self.format_token_url())
        # self.check_state()
        # todo add cache..
        if code := result.code:
            response = yield self.build_access_token_request(code)
            if response.is_success:
                response.read()  # todo investigate
                token = response.json().get(self.token_field_name, None)
                request.headers[self.header_name] = self.header_value.format(
                    token=token
                )
        yield request

    async def async_auth_flow(
        self, request: Request
    ) -> typing.AsyncGenerator[Request, Response]:
        result = await self.server.async_get_authorization_grant(
            self.format_token_url()
        )
        # self.check_state()
        if code := result.code:
            response = yield self.build_access_token_request(code)
            if response.is_success:
                await response.aread()
                token = response.json().get(self.token_field_name, None)
                request.headers[self.header_name] = self.header_value.format(
                    token=token
                )
        yield request

    def build_access_token_request(self, code):
        r = Request(
            method="POST",
            url=self.exchange_url,
            headers=self.get_client_credentials_headers(),
            data=self.get_client_credentials_body(code)
        )
        return r

    # todo obsolete..
    def get_authorization_grant(self):
        return self.server.get_authorization_grant(self.format_token_url())

    async def async_get_authorization_grant(self):
        return await self.server.async_get_authorization_grant(self.format_token_url())

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

    def check_state(self):
        if self.state != self.server.received_state:
            raise ValueError("State Mismatch")


class VimeoOauth2ImplicitGrant(httpx.Auth):
    authorization_url = "https://api.vimeo.com/oauth/authorize?" \
                        "response_type=token" \
                        "&client_id={client_id}" \
                        "&redirect_uri={redirect_uri}" \
                        "&state={state}" \
                        "&scope={scope}"
    server_address = "http://127.0.0.1:5555"
    header_name = "Authorization"
    header_value = "Bearer {token}"
    default_scope = "public private"

    def __init__(self, client_id, client_secret, state, scope=None, server=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.state = state
        self.redirect_uri = self.server_address
        self.scope = (
            " ".join(scope) if scope and isinstance(scope, list) else self.default_scope
        )

        self.server = server or Server(redirect_on_fragment=True)

    def sync_auth_flow(
            self, request: Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        result = self.server.get_authorization_grant(self.format_token_url())
        if access_token := result.access_token:
            request.headers[self.header_name] = self.header_value.format(
                token=access_token
            )
        yield request

    async def async_auth_flow(
        self, request: Request
    ) -> typing.AsyncGenerator[Request, Response]:
        result = await self.server.async_get_authorization_grant(
            self.format_token_url()
        )
        if access_token := result.access_token:
            request.headers[self.header_name] = self.header_value.format(
                token=access_token
            )
        yield request

    def format_token_url(self) -> str:
        return self.authorization_url.format(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            state=self.state,
            scope=self.scope,
        )


class VimeoOauth2DeviceCodeGrant(httpx.Auth):
    requires_response_body = True
    exchange_url = "https://api.vimeo.com/oauth/device"
    default_scope = "public private"
    header_name = "Authorization"
    header_value = "Bearer {token}"
    token_field_name = "access_token"
    server_address = "http://127.0.0.1:5555"

    def __init__(self, client_id, client_secret, state, scope=None, server=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.state = state
        self.redirect_uri = self.server_address
        self.scope = (
            " ".join(scope) if scope and isinstance(scope, list) else self.default_scope
        )

        self.server = server or Server()

    def sync_auth_flow(
            self, request: Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        response = yield self.build_user_code_request()
        response.read()
        payload = DeviceCodeGrantResponse(**response.json())
        self.print_instructions(payload.activate_link, payload.user_code)
        response = self.server.poll_authorize_url(
            url=payload.authorize_link,
            expires_in=payload.expires_in,
            interval=payload.interval,
            headers=self.get_device_code_auth_headers(),
            data={"user_code": payload.user_code, "device_code": payload.device_code},
        )
        token = response.json().get(self.token_field_name, None)
        if token:
            request.headers[self.header_name] = self.header_value.format(token=token)
        yield request

    async def async_auth_flow(
        self, request: Request
    ) -> typing.AsyncGenerator[Request, Response]:
        response = yield self.build_user_code_request()
        await response.aread()
        payload = DeviceCodeGrantResponse(**response.json())
        self.print_instructions(payload.activate_link, payload.user_code)

        response = await self.server.async_poll_authorize_url(
            url=payload.authorize_link,
            expires_in=payload.expires_in,
            interval=payload.interval,
            headers=self.get_device_code_auth_headers(),
            data={"user_code": payload.user_code, "device_code": payload.device_code},
        )
        token = response.json().get(self.token_field_name, None)
        if token:
            request.headers[self.header_name] = self.header_value.format(token=token)
        yield request

    def build_user_code_request(self):
        r = Request(
            method="POST",
            url=self.exchange_url,
            headers=self.get_device_code_auth_headers(),
            data=self.get_device_code_auth_body()
        )
        return r

    def get_device_code_auth_headers(self):
        encoded = _encode_client_credentials(self.client_id, self.client_secret)
        headers = {
            "Authorization": f"basic {encoded}",
            "Accept": "application/vnd.vimeo.*+json;version=3.4",
        }
        return headers

    def get_device_code_auth_body(self):
        body = {
            "grant_type": "device_grant",
            "scope": self.scope
        }
        return body

    def print_instructions(self, activate_link, code):
        sys.stdout.write(f"> open the following link {activate_link}\n")
        sys.stdout.write(f"> and insert this code: {code}\n")
