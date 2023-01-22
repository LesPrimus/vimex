import io

import httpx
import pytest

import vimex


class TestSyncTusUpload:
    def test_create_upload_link_200(self, respx_mock):
        stream = io.BytesIO(b"Hello World!")

        client = vimex.VimeoClient()
        respx_mock.post(client.upload_url).mock(
            return_value=httpx.Response(
                200,
                json={
                    "upload": {"upload_link": "some_upload_link"},
                    "uri": "some_upload_uri",
                },
            )
        )
        upload_link, uri = client.create_upload_link(stream, "tus")
        assert upload_link == "some_upload_link"
        assert uri == "some_upload_uri"

    def test_create_upload_link_400(self, respx_mock):
        stream = io.BytesIO(b"Hello World!")

        client = vimex.VimeoClient()
        respx_mock.post(client.upload_url).mock(
            return_value=httpx.Response(400, json={"details": "some_error"})
        )
        with pytest.raises(vimex.UploadException):
            client.create_upload_link(stream, "tus")
        # assert upload_link == "some_upload_link"
        # assert uri == "some_upload_uri"
