import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import analyze

spec = importlib.util.spec_from_file_location("local_media", ROOT / "src/video_analysis/local_media.py")
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


class LocalMediaTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.png = self.root / "A frame.PNG"
        Image.new("RGB", (16, 16)).save(self.png)

    def test_enumeration_selects_regular_files_with_configured_extensions(self):
        (self.root / "alias.png").symlink_to(self.png)
        (self.root / "directory.png").mkdir()
        with patch.object(analyze, "load_config", return_value=object()):
            self.assertEqual(analyze.get_video_files(self.root), [str(self.png)])

    def test_snapshot_is_private_stable_and_removed(self):
        expected = self.png.read_bytes()
        with media.selected_media(self.png) as path:
            copied = Path(path)
            self.png.unlink()
            self.assertEqual(copied.read_bytes(), expected)
            self.assertEqual(copied.parent.stat().st_mode & 0o077, 0)
        self.assertFalse(copied.exists())

    def test_directory_input_closes_descriptor(self):
        folder = self.root / "folder.png"
        folder.mkdir()
        opened = []
        original_open = os.open

        def track_open(*args, **kwargs):
            fd = original_open(*args, **kwargs)
            opened.append(fd)
            return fd

        with patch.object(media.os, "open", track_open):
            with self.assertRaises(ValueError), media.selected_media(folder):
                self.fail("unexpected folder")
        self.assertEqual(len(opened), 1)
        with self.assertRaises(OSError):
            os.fstat(opened[0])

    def test_selected_folder_identity(self):
        source = self.root / "frames"
        source.mkdir()
        self.png.rename(source / self.png.name)
        fd = os.open(source, os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, fd)
        source.rename(self.root / "renamed")
        with media.selected_media(source / self.png.name, directory_fd=fd) as path:
            with Image.open(path) as image:
                self.assertEqual(image.size, (16, 16))

    def test_refuses_symlinks_and_plain_text(self):
        alias = self.root / "alias.png"
        alias.symlink_to(self.png)
        with self.assertRaises(OSError), media.selected_media(alias):
            self.fail("unexpected media")
        for suffix in (".mp4", ".png"):
            with self.subTest(suffix=suffix):
                path = self.root / ("notes" + suffix)
                path.write_text("Ordinary text with no media.")
                with self.assertRaises((OSError, subprocess.CalledProcessError)), media.selected_media(path):
                    self.fail("unexpected media")

    def test_supported_video_streams_survive(self):
        for suffix, codec in [("mp4", "mpeg4"), ("mov", "mpeg4"), ("avi", "mpeg4"),
                              ("webm", "libvpx"), ("mkv", "mpeg4"), ("gif", "gif")]:
            with self.subTest(suffix=suffix):
                path = self.root / ("synthetic." + suffix)
                subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                                "color=s=32x32:d=0.2", "-c:v", codec, str(path)], check=True)
                with media.selected_media(path) as copied:
                    dims = subprocess.check_output([
                        "ffprobe", "-v", "error", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", copied], text=True).strip()
                    self.assertEqual(dims, "32,32")
