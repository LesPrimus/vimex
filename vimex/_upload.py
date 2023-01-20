import os
from typing import Optional, IO

import httpx
from tusclient.uploader import Uploader as TusPyUploader
from tusclient.uploader import AsyncUploader as AsyncTusPyUploader
from tusclient.uploader.baseuploader import BaseUploader as TusPyBaseUploader

import vimex

from ._utils import get_attribute


class BaseUpload:
    upload_url = "https://api.vimeo.com/me/videos"

    @staticmethod
    def get_post_upload_body(file_size, approach):
        body = {"upload": {"approach": str(approach), "size": str(file_size)}}
        return body

    @staticmethod
    def get_file_size(filename):
        try:
            return os.path.getsize(filename)
        except TypeError:
            return len(filename.read())

    def create_upload_link(self, size, approach, **kwargs):
        body = self.get_post_upload_body(size, approach)
        response = self.post(self.upload_url, json=body, **kwargs)
        return response

    async def async_create_upload_link(self, size, approach, **kwargs):
        body = self.get_post_upload_body(size, approach)
        response = await self.post(self.upload_url, json=body, **kwargs)
        return response

    @staticmethod
    def get_value_from_response(response: httpx.Response, *args) -> str:
        if not response.is_success:
            raise vimex.TusUploadException(response.json())
        return get_attribute(response.json(), *args)

    @staticmethod
    def init_uploader(uploader_cls, *args, **kwargs):
        return uploader_cls(*args, **kwargs)


class SyncUploadMixin(BaseUpload):
    def tus_upload(
        self,
        file_path: Optional[str] = None,
        file_stream: Optional[IO] = None,
        uploader_class: Optional[TusPyBaseUploader] = TusPyUploader,
        uploader_config: Optional[dict] = None,
        **kwargs,
    ):
        assert file_path or file_stream

        size = self.get_file_size(file_path or file_stream)

        response = self.create_upload_link(size, approach="tus", **kwargs)
        upload_link = self.get_value_from_response(response, "upload", "upload_link")
        uri = self.get_value_from_response(response, "uri")

        uploader = self.init_uploader(
            uploader_class,
            file_path=file_path,
            file_stream=file_stream,
            url=upload_link,
            **uploader_config or {},
        )
        while uploader.offset < uploader.stop_at:
            uploader.upload_chunk()
        return uri


class AsyncUploadMixin(BaseUpload):
    async def tus_upload(
        self,
        file_path: Optional[str] = None,
        file_stream: Optional[IO] = None,
        uploader_class: Optional[TusPyBaseUploader] = AsyncTusPyUploader,
        uploader_config: Optional[dict] = None,
        **kwargs,
    ):
        assert file_path or file_stream

        size = self.get_file_size(file_path or file_stream)

        response = await self.async_create_upload_link(size, approach="tus", **kwargs)
        upload_link = self.get_value_from_response(response, "upload", "upload_link")
        uri = self.get_value_from_response(response, "uri")

        uploader = self.init_uploader(
            uploader_class,
            file_path=file_path,
            file_stream=file_stream,
            url=upload_link,
            **uploader_config or {},
        )
        while uploader.offset < uploader.stop_at:
            await uploader.upload_chunk()
        return uri
