import threading
from enum import Enum, auto
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
from urllib.parse import urlparse, parse_qs

from ._exceptions import AuthorizationCodeException, AuthorizationStateException

HOST = "localhost"
PORT = 5555

logger = logging.getLogger(__name__)

# TODO
# refactor do_GET


class ServerFlow(Enum):
    CODE = auto()
    IMPLICIT = auto()


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self) -> None:
        flow_handler = self.get_flow(self.server.flow)
        try:
            flow_handler()
        except Exception as exc:
            self.send_html(400, str(exc))
            # something went wrong stop the local server.
            self.server.event.set()
        else:
            self.send_html(200, "You can close this page..")

    def get_flow(self, flow: ServerFlow):
        return {
            ServerFlow.CODE: self.handle_code_grant,
            ServerFlow.IMPLICIT: self.handle_implicit_grant
        }[flow]

    def handle_code_grant(self):
        query_param_name = "code"
        code, state = self.parse_query_components(query_param_name)
        self.server.grant = (code, state)
        self.server.event.set()

    def handle_implicit_grant(self):
        if self.server.redirect_on_fragment is True:
            self.send_html(200, self.get_fragment_redirect_page())
            self.server.redirect_on_fragment = False
        else:
            query_param_name = "access_token"
            code, state = self.parse_query_components(query_param_name)
            self.server.grant = (code, state)
            self.server.event.set()

    def get_fragment_redirect_page(self) -> str:
        return """<html><body><script>
        var new_url = window.location.href.replace("#","");
        window.location.replace(new_url)
        </script></body></html>"""

    def send_html(self, code: int, html_content: str) -> None:
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(str.encode(html_content))
        logger.debug("HTML content sent to client.")

    def parse_query_components(self, query_param_name):
        query_components = parse_qs(urlparse(self.path).query)
        try:
            grant_param = query_components.get(query_param_name, None)[0]
        except TypeError:
            raise AuthorizationCodeException("Unable to retrieve the auth code from url param.")
        try:
            state = query_components.get("state")[0]
        except TypeError:
            raise AuthorizationStateException("Unable to retrieve the state param from url.")
        return grant_param, state


class Server(HTTPServer):
    def __init__(self, flow: ServerFlow, redirect_on_fragment=False):
        # todo make (host, port) configurable for the client.
        super().__init__((HOST, PORT), RequestHandler)
        self.flow = flow
        self.redirect_on_fragment = redirect_on_fragment
        self.grant = None
        self.event = threading.Event()
        logger.debug(f"Listening on {self.server_address}..")
