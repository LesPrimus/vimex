import os
from typing import Optional, IO

from tusclient.uploader import Uploader as TusPyUploader
from tusclient.uploader.baseuploader import BaseUploader as TusPyBaseUploader

from rich.progress import Progress

import vimex


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


class SyncUploadMixin(BaseUpload):
    def tus_upload(
        self,
        file_path: Optional[str] = None,
        file_stream: Optional[IO] = None,
        uploader_class: Optional[TusPyBaseUploader] = None,
        uploader_config: Optional[dict] = None,
        **kwargs,
    ):
        assert file_path or file_stream

        uploader_class = uploader_class or TusPyUploader

        uploader_config = uploader_config or {}
        uploader_config.pop("file_path", None)
        uploader_config.pop("file_stream", None)

        size = self.get_file_size(file_path or file_stream)

        response = self.create_upload_link(size, approach="tus", **kwargs)

        if not response.is_success:
            raise vimex.TusUploadException(response.json())
        try:
            upload_link = response.json()["upload"]["upload_link"]
        except KeyError:
            raise vimex.TusUploadException("no upload link provided from vimeo.")

        try:
            uri = response.json()["uri"]
        except KeyError:
            raise vimex.TusUploadException("no uri link provided from vimeo")

        uploader = uploader_class(
            file_path=file_path,
            file_stream=file_stream,
            url=upload_link,
            **uploader_config,
        )
        with Progress() as progress:
            task = progress.add_task("[green]Uploading...", total=uploader.stop_at)
            while not progress.finished:
                progress.update(task, advance=uploader.offset)
                uploader.upload_chunk()
        return uri


class AsyncUploadMixin(BaseUpload):
    pass
