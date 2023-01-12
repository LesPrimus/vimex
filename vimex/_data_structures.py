from dataclasses import dataclass
from typing import NamedTuple


class DeviceCodeGrantResponse(NamedTuple):
    device_code: str
    user_code: str
    authorize_link: str
    activate_link: str
    expires_in: int
    interval: int


@dataclass
class ServerFlowResult:
    code: str = None
    received_state: str = None
    access_token: str = None
