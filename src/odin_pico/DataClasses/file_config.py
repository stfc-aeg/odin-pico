"""Store settings for the file to write PicoScope data onto."""

from dataclasses import dataclass


@dataclass
class FileConfig:
    file_name: str = ""
    folder_name: str = ""
    _file_path: str = ""
    curr_file_name: str = ""
    last_write_success: bool = False
    temp_suffix: str = None   # e.g. "_25-0c"
    repeat_suffix: str = None   # e.g. "_3"

    @property
    def file_path(self) -> str:
        return self._file_path

    @file_path.setter
    def file_path(self, value: str):
        self._file_path = value