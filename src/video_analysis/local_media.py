"""Keep decoders and analysis clients within the operator's selected local input."""

from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

from PIL import Image


# Pin the input demuxer. Downstream readers receive a standalone file generated
# by ffmpeg, with only the selected picture and audio streams.
VIDEO_FORMATS = {
    ".mp4": ("mov", "mp4"),
    ".mov": ("mov", "mov"),
    ".avi": ("avi", "avi"),
    ".mkv": ("matroska", "matroska"),
    ".webm": ("matroska", "webm"),
    ".gif": ("gif", "gif"),
}
IMAGE_FORMATS = {
    ".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG",
    ".bmp": "BMP", ".webp": "WEBP", ".tiff": "TIFF",
}


@contextmanager
def selected_media(path, *, directory_fd=None, temp_dir=None):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in VIDEO_FORMATS and suffix not in IMAGE_FORMATS:
        raise ValueError("Unsupported local media format")

    # Batch enumeration and the subsequent open share one directory descriptor.
    # O_NONBLOCK lets us reject non-regular files before trying to consume them.
    source_name = path if directory_fd is None else path.name
    fd = os.open(source_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("Media input must be a regular local file")
        source = os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise
    with source:
        with tempfile.TemporaryDirectory(dir=temp_dir) as work:
            target = Path(work, path.name)
            if suffix in IMAGE_FORMATS:
                with target.open("xb") as output:
                    shutil.copyfileobj(source, output)
                with Image.open(target, formats=[IMAGE_FORMATS[suffix]]) as image:
                    image.verify()
            else:
                demuxer, muxer = VIDEO_FORMATS[suffix]
                # The inherited descriptor supports seeking and fixes input identity.
                options = ["-enable_drefs", "0", "-use_absolute_path", "0"] if demuxer == "mov" else []
                subprocess.run([
                    "ffmpeg", "-nostdin", "-v", "error", "-protocol_whitelist", "file",
                    "-format_whitelist", demuxer, "-f", demuxer, *options,
                    "-i", f"/dev/fd/{fd}", "-map", "0:v:0", "-map", "0:a?",
                    "-map_metadata", "-1", "-map_chapters", "-1", "-c", "copy",
                    "-f", muxer, str(target.resolve()),
                ], pass_fds=(fd,), check=True, stderr=subprocess.PIPE)
            yield str(target.resolve())
