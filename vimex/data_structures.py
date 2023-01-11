from typing import NamedTuple


class DeviceCodeGrantResponse(NamedTuple):
    device_code: str
    user_code: str
    authorize_link: str
    activate_link: str
    expires_in: int
    interval: int
