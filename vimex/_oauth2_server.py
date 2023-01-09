import threading
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
from urllib.parse import urlparse, parse_qs

from ._exceptions import AuthorizationCodeException, AuthorizationStateException

HOST = "localhost"
PORT = 5555

logger = logging.getLogger(__name__)

# TODO
# refactor do_GET


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.grant_name = kwargs.pop("grant_name", None)
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        try:
            code, state = self.parse_query_components()
        except Exception as exc:
            self.send_html(400, str(exc))
            self.server.event.set()
            return
        self.server.event.set()
        self.server.grant = (code, state)
        self.send_html(200, "You can close this page..")

    def send_html(self, code: int, html_content: str) -> None:
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(str.encode(html_content))
        logger.debug("HTML content sent to client.")

    def parse_query_components(self):
        query_components = parse_qs(urlparse(self.path).query)
        try:
            grant_param = query_components.get(self.grant_name, None)[0]
        except TypeError:
            raise AuthorizationCodeException("Unable to retrieve the auth code from url param.")
        try:
            state = query_components.get("state")[0]
        except TypeError:
            raise AuthorizationStateException("Unable to retrieve the state param from url.")
        return grant_param, state


class Server(HTTPServer):
    def __init__(self, grant_name):
        self.grant_name = grant_name
        super().__init__((HOST, PORT), partial(RequestHandler, grant_name=grant_name))
        self.grant = None
        self.event = threading.Event()
        logger.debug(f"Listening on {self.server_address}..")
