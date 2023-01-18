from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class GrantType(Enum):
    CLIENT_CREDENTIALS = "client_credentials"
    AUTHORIZATION_CODE = "authorization_code"
    IMPLICIT = "implicit"
    DEVICE = "device_grant"


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


class TusUploadResponse(NamedTuple):
    pass
