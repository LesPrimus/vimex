import base64
import sys
import typing
from typing import Generator
import logging
import httpx

from httpx import Request, Response

from ._oauth2_server import Server
from ._data_structures import DeviceCodeGrantResponse, GrantType

logger = logging.getLogger(__name__)


def _encode_client_credentials(client_id: str, client_secret: str) -> str:
    return base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()


class BaseOauth2Auth(httpx.Auth):
    access_token_url: str
    grant_type: GrantType

    token_field_name = "access_token"
    header_name = "Authorization"
    header_value = "Bearer {token}"
    default_scope = "public private"
    server_host = "http://127.0.0.1"
    server_port = 5555

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        state: str,
        access_token: typing.Optional[str] = None,
        scope: typing.Optional[list[str]] = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.state = state
        self.access_token = access_token
        self.scope = (
            " ".join(scope) if scope and isinstance(scope, list) else self.default_scope
        )

    def sync_auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        token = self.sync_get_token()
        if token:
            request.headers[self.header_name] = self.header_value.format(token=token)
        yield request

    async def async_auth_flow(
        self, request: Request
    ) -> typing.AsyncGenerator[Request, Response]:
        token = await self.async_get_token()
        if token:
            request.headers[self.header_name] = self.header_value.format(token=token)
        yield request

    def sync_get_token(self):
        raise NotImplementedError

    async def async_get_token(self):
        raise NotImplementedError

    def build_access_token_request(
        self, method: str, url: str, headers: dict, body: dict, **kwargs
    ):
        r = Request(
            method=method,
            url=url,
            headers=headers,
            data=body,
        )
        return r

    @staticmethod
    def send_request(request, *args, **kwargs):
        _client, _auto_created = kwargs.pop("client", None), False
        if _client is None:
            _client, _auto_created = httpx.Client(), True
        try:
            return _client.send(request, *args, **kwargs)
        finally:
            if _auto_created:
                _client.close()

    @staticmethod
    async def async_send_request(request, *args, **kwargs):
        _client, _auto_created = kwargs.pop("client", None), False
        if _client is None:
            _client, _auto_created = httpx.AsyncClient(), True
        try:
            return await _client.send(request, *args, **kwargs)
        finally:
            if _auto_created:
                await _client.aclose()

    def get_authorization_headers(self):
        encoded = _encode_client_credentials(self.client_id, self.client_secret)
        headers = {
            "Authorization": f"basic {encoded}",
            "Accept": "application/vnd.vimeo.*+json;version=3.4",
        }
        return headers

    def get_authorization_body(self, *args, **kwargs) -> dict:
        return {"grant_type": self.grant_type.value, "scope": self.scope}

    def check_state(self, received_state):
        if self.state != received_state:
            raise ValueError("State Mismatch")

    @property
    def redirect_uri(self):
        return f"http://{self.server.host}:{self.server.port}"

    @property
    def server(self):
        return self._server

    @server.setter
    def server(self, server):
        self._server = server


class VimeoOAuth2ClientCredentials(BaseOauth2Auth):
    access_token_url = "https://api.vimeo.com/oauth/authorize/client"
    default_scope = "public"
    grant_type = GrantType.CLIENT_CREDENTIALS

    def sync_get_token(self):
        if self.access_token is None:
            response = self.send_request(self.build_access_token_request())
            if response.is_success:
                response.read()
                token = response.json().get(self.token_field_name, None)
                self.access_token = token
        return self.access_token

    async def async_get_token(self):
        if self.access_token is None:
            response = await self.async_send_request(self.build_access_token_request())
            if response.is_success:
                await response.aread()
                token = response.json().get(self.token_field_name, None)
                self.access_token = token
        return self.access_token

    def build_access_token_request(self, *args, **kwargs):
        return super().build_access_token_request(
            method="POST",
            url=self.access_token_url,
            headers=self.get_authorization_headers(),
            body=self.get_authorization_body(),
        )


class VimeoOauth2AuthorizationCode(BaseOauth2Auth):
    requires_response_body = True
    requires_request_body = True
    authorization_url = (
        "https://api.vimeo.com/oauth/authorize?"
        "response_type=code"
        "&client_id={client_id}"
        "&redirect_uri={redirect_uri}"
        "&state={state}"
        "&scope={scope}"
    )

    exchange_url = "https://api.vimeo.com/oauth/access_token"
    grant_type = GrantType.AUTHORIZATION_CODE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server = Server(
            port=self.server_port,
        )

    def sync_get_token(self):
        if self.access_token is None:
            result = self._server.get_authorization_grant(
                self.format_authorization_url()
            )
            if code := result.code:
                response = self.send_request(self.build_access_token_request(code))
                if response.is_success:
                    response.read()
                    token = response.json().get(self.token_field_name, None)
                    self.access_token = token
        return self.access_token

    async def async_get_token(self):
        if self.access_token is None:
            result = await self.server.async_get_authorization_grant(
                self.format_authorization_url()
            )
            if code := result.code:
                response = await self.async_send_request(
                    self.build_access_token_request(code)
                )
                if response.is_success:
                    await response.aread()
                    token = response.json().get(self.token_field_name, None)
                    self.access_token = token
        return self.access_token

    def build_access_token_request(self, code, *args, **kwargs):
        return super().build_access_token_request(
            method="POST",
            url=self.exchange_url,
            headers=self.get_authorization_headers(),
            body=self.get_authorization_body(code),
        )

    def format_authorization_url(self) -> str:
        return self.authorization_url.format(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            state=self.state,
            scope=self.scope,
        )

    def get_authorization_body(self, code, *args, **kwargs) -> dict:
        return {
            "code": str(code),
            "redirect_uri": str(self.redirect_uri),
            **super().get_authorization_body(),
        }


class VimeoOauth2ImplicitGrant(BaseOauth2Auth):
    authorization_url = "https://api.vimeo.com/oauth/authorize?" \
                        "response_type=token" \
                        "&client_id={client_id}" \
                        "&redirect_uri={redirect_uri}" \
                        "&state={state}" \
                        "&scope={scope}"
    grant_type = GrantType.IMPLICIT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server = Server(port=self.server_port, redirect_on_fragment=True)

    def sync_get_token(self):
        if self.access_token is None:
            result = self._server.get_authorization_grant(
                self.format_authorization_url()
            )
            if access_token := result.access_token:
                self.access_token = access_token
        return self.access_token

    async def async_get_token(self):
        if self.access_token is None:
            result = await self.server.async_get_authorization_grant(
                self.format_authorization_url()
            )
            if access_token := result.access_token:
                self.access_token = access_token
        return self.access_token

    def format_authorization_url(self) -> str:
        return self.authorization_url.format(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            state=self.state,
            scope=self.scope,
        )


class VimeoOauth2DeviceCodeGrant(BaseOauth2Auth):
    requires_response_body = True
    access_token_url = "https://api.vimeo.com/oauth/device"
    grant_type = GrantType.DEVICE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server = Server(port=self.server_port)

    def sync_get_token(self):
        if self.access_token is None:
            response = self.send_request(self.build_access_token_request())
            if response.is_success:
                response.read()
                payload = DeviceCodeGrantResponse(**response.json())
                self.print_instructions(payload.activate_link, payload.user_code)
                response = self._server.poll_authorize_url(
                    url=payload.authorize_link,
                    expires_in=payload.expires_in,
                    interval=payload.interval,
                    headers=self.get_authorization_headers(),
                    data={
                        "user_code": payload.user_code,
                        "device_code": payload.device_code,
                    },
                )
                if response.is_success:
                    response.read()
                    token = response.json().get(self.token_field_name, None)
                    self.access_token = token
        return self.access_token

    async def async_get_token(self):
        if self.access_token is None:
            response = await self.async_send_request(self.build_access_token_request())
            if response.is_success:
                await response.aread()
                payload = DeviceCodeGrantResponse(**response.json())
                self.print_instructions(payload.activate_link, payload.user_code)

                response = await self._server.async_poll_authorize_url(
                    url=payload.authorize_link,
                    expires_in=payload.expires_in,
                    interval=payload.interval,
                    headers=self.get_authorization_headers(),
                    data={
                        "user_code": payload.user_code,
                        "device_code": payload.device_code,
                    },
                )
                if response.is_success:
                    token = response.json().get(self.token_field_name, None)
                    self.access_token = token
        return self.access_token

    def build_access_token_request(self, *args, **kwargs):
        return super().build_access_token_request(
            method="POST",
            url=self.access_token_url,
            headers=self.get_authorization_headers(),
            body=self.get_authorization_body(),
        )

    def print_instructions(self, activate_link, code):
        sys.stdout.write(f"> open the following link {activate_link}\n")
        sys.stdout.write(f"> and insert this code: {code}\n")
