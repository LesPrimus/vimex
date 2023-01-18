import httpx

from ._upload import SyncUploadMixin, AsyncUploadMixin


class VimeoClient(SyncUploadMixin, httpx.Client):
    pass


class AsyncVimeoClient(AsyncUploadMixin, httpx.AsyncClient):
    pass
