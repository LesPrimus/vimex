import asyncio
import sys
import webbrowser
import time
import logging
from typing import Optional

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.routing import Route

from ._data_structures import ServerFlowResult


logger = logging.getLogger(__name__)


class Server:
    def __init__(self, port: int, redirect_on_fragment=False):
        self._redirect_on_fragment = redirect_on_fragment
        self._routes = [
            Route("/", self.callback),
        ]

        self._app = Starlette(routes=self._routes)
        self._config = uvicorn.Config(app=self._app, port=port)
        self._server = uvicorn.Server(self._config)

        # Response from vimeo.
        self.result = ServerFlowResult()

    def implicit_grant_redirect(self):
        self._redirect_on_fragment = False
        return HTMLResponse(
            """<html><body><script>
        var new_url = window.location.href.replace("#","");
        window.location.replace(new_url)
        </script></body></html>"""
        )

    async def callback(self, request: Request):
        if self._redirect_on_fragment:
            return self.implicit_grant_redirect()
        self.result.code = request.query_params.get("code")
        self.result.received_state = request.query_params.get("state")
        self.result.access_token = request.query_params.get("access_token")
        self.stop()
        return JSONResponse({"details": "Success"})

    @property
    def host(self):
        return self._server.config.host

    @property
    def port(self):
        return self._server.config.port

    def run(self):
        self._server.run()

    def stop(self):
        self._server.should_exit = True

    async def serve(self):
        await self._server.serve()

    async def shutdown(self):
        await self._server.shutdown()

    def get_authorization_grant(self, link) -> ServerFlowResult:
        self.open_link(link)
        self.run()
        return self.result

    async def async_get_authorization_grant(self, link) -> ServerFlowResult:
        await asyncio.to_thread(self.open_link, link)
        await self.serve()
        return self.result

    def open_link(self, link):
        webbrowser.open(link)

    def poll_authorize_url(
        self,
        url: str,
        expires_in: int,
        interval: int,
        headers=None,
        data=None,
    ):
        timeout_sec = expires_in
        start = time.monotonic()

        with httpx.Client() as client:
            while time.monotonic() < start + timeout_sec:
                sys.stdout.write(f"Polling {url}..")
                response = client.post(url, headers=headers, data=data)
                if response.is_success:
                    return response
                time.sleep(interval)
        raise TimeoutError(f"The polling to {url} timeout..")

    async def async_poll_authorize_url(
        self,
        url: str,
        expires_in: int,
        interval: int,
        headers=None,
        data=None,
    ):
        timeout_sec = expires_in
        start = time.monotonic()

        async with httpx.AsyncClient() as client:
            while time.monotonic() < start + timeout_sec:
                sys.stdout.write(f"Polling {url}..")
                response = await client.post(url=url, headers=headers, data=data)
                if response.is_success:
                    return response
                await asyncio.sleep(interval)
        raise TimeoutError(f"The polling to {url} timeout..")


class MockedCallBackServer:
    def __init__(self, code, state):
        self.code = code
        self.state = state

    def get_authorization_grant(self, *args, **kwargs):
        return self.code, self.state
