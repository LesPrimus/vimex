import os
import sys
from functools import cached_property
from typing import IO, Union

import httpx

import vimex
from ._utils import get_attribute, get_file_stream, get_file_size


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

    @staticmethod
    def get_value_from_response(response: httpx.Response, *args) -> str:
        if not response.is_success:
            raise vimex.UploadException(response.json())
        return get_attribute(response.json(), *args)


class SyncUploadMixin(BaseUpload):
    def create_video(self, file: Union[str, IO], approach, **kwargs):
        size = get_file_size(file)
        body = self.get_post_upload_body(size, approach)
        response = self.post(self.upload_url, json=body, **kwargs)
        upload_link = self.get_value_from_response(response, "upload", "upload_link")
        uri = self.get_value_from_response(response, "uri")
        return upload_link, uri

    def perform_upload(self, file, upload_link, uploader=None):
        uploader = uploader or TusUploader(file, upload_link, client=self)
        return uploader.upload()

    def tus_upload(self, file, uploader=None):
        upload_link, uri = self.create_video(file, "tus")
        return self.perform_upload(file, upload_link, uploader)


class AsyncUploadMixin(BaseUpload):
    pass


class TusUploader:
    def __init__(self, file, upload_link: str, client, chunk_size=sys.maxsize):
        self._file = file
        self.chunk_size = chunk_size
        self.upload_link = upload_link
        self.client = client
        self.upload_offset = 0

    @cached_property
    def file(self):
        return get_file_stream(self._file)

    @cached_property
    def file_length(self):
        return get_file_size(self.file)

    def set_headers(self, **kwargs):
        content_length = kwargs.pop("content_length", None)
        headers = {
            "Tus-Resumable": "1.0.0",
            "Upload-Offset": str(self.upload_offset),
            "Content-Type": "application/offset+octet-stream",
            **kwargs,
        }
        if content_length:
            headers.update({"Content-length": content_length})
        return headers

    def get_content_length(self):
        remain = self.file_length - self.upload_offset
        return self.chunk_size if remain > self.chunk_size else remain

    def chunks_upload(self):
        while self.upload_offset < self.file_length:
            chunk = self.file.read(self.get_content_length())
            response = self.client.patch(
                self.upload_link,
                headers=self.set_headers(content_length=str(self.get_content_length())),
                data=chunk,
            )
            self.upload_offset = int(response.headers["upload-offset"])
            yield self.upload_offset, self.file_length
