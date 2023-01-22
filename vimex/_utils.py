import os
from typing import Union

from typing.io import IO


def get_attribute(instance, *attrs):
    for attr in attrs:
        try:
            instance = instance[attr]
        except TypeError:
            raise KeyError(f"{attr}")
    return instance


def get_file_stream(file: Union[str, IO]):
    if hasattr(file, "read"):
        file.seek(0)
        return file
    if os.path.isfile(file):
        return open(file, "rb")
    raise ValueError("Invalid file.")


def get_file_size(file: Union[str, IO]):
    file = get_file_stream(file)
    pos = file.tell()
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(pos)
    return size
