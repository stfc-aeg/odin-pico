"""Store settings for the file to write PicoScope data onto."""

from dataclasses import dataclass


@dataclass
class FileConfig:
    file_name: str = ""
    folder_name: str = ""
    file_path: str = ""
    curr_file_name: str = ""
    last_write_success: bool = False
    temp_suffix: str = None   # e.g. "_25-0c"
    repeat_suffix: str = None   # e.g. "_3"
