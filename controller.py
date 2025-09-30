"""Shared backend logic for SpeedTake audio extraction."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import sys
from typing import Callable, Dict, Iterable, List, Optional, Tuple

StatusCallback = Callable[[int, int, str], None]
ProgressCallback = Callable[[int, int], None]
ErrorCallback = Callable[[str, Exception], None]


@dataclass
class ExtractionResult:
    """Container for extraction results."""

    success_count: int
    total_files: int
    last_output_path: Optional[str]
    errors: List[str] = field(default_factory=list)


class SpeedTakeController:
    """Encapsulates the extraction workflow shared by multiple front-ends."""

    VIDEO_EXTENSIONS = {
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
    }

    AUDIO_CODECS: Dict[str, str] = {
        "mp3": "libmp3lame",
        "wav": "pcm_s16le",
        "flac": "flac",
        "aac": "aac",
    }

    def __init__(self) -> None:
        self.selected_files: List[str] = []
        self.output_format: str = "mp3"
        self.output_folder: Optional[str] = None
        self.ffmpeg_path: Optional[str] = None

    # ----------------------------
    # Selection helpers
    # ----------------------------
    def add_files(self, files: Iterable[str]) -> List[str]:
        """Add video files to the selection, returning the new additions."""

        new_files: List[str] = []
        for file in files:
            file_path = str(file)
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                new_files.append(file_path)
        return new_files

    def add_folder(self, folder: str) -> Tuple[List[str], int]:
        """Add all supported video files from a folder.

        Returns a tuple of (new_files, total_video_files).
        """

        if not folder:
            return [], 0

        folder_path = Path(folder)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder}")

        video_files = [
            str(path)
            for path in folder_path.glob("**/*")
            if path.suffix.lower() in self.VIDEO_EXTENSIONS
        ]
        return self.add_files(video_files), len(video_files)

    def clear_files(self) -> None:
        self.selected_files.clear()

    # ----------------------------
    # Configuration
    # ----------------------------
    def set_output_folder(self, folder: Optional[str]) -> None:
        self.output_folder = folder or None

    def set_output_format(self, fmt: str) -> None:
        if fmt not in self.AUDIO_CODECS:
            raise ValueError(f"Unsupported format: {fmt}")
        self.output_format = fmt

    # ----------------------------
    # FFmpeg handling
    # ----------------------------
    def check_ffmpeg(self, exe_dir: Optional[Path] = None) -> bool:
        """Locate a working ffmpeg binary."""

        search_candidates: List[str] = []
        if exe_dir:
            candidate = exe_dir / "ffmpeg.exe"
            if candidate.exists():
                search_candidates.append(str(candidate))
        search_candidates.append("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")

        for candidate in search_candidates:
            try:
                kwargs = {}
                if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
                    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                subprocess.run(
                    [candidate, "-version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                    **kwargs,
                )
                self.ffmpeg_path = candidate
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        self.ffmpeg_path = None
        return False

    # ----------------------------
    # Extraction
    # ----------------------------
    def extract_audio_files(
        self,
        status_callback: Optional[StatusCallback] = None,
        progress_callback: Optional[ProgressCallback] = None,
        error_callback: Optional[ErrorCallback] = None,
    ) -> ExtractionResult:
        """Extract audio for the selected files."""

        total_files = len(self.selected_files)
        success_count = 0
        last_output_path: Optional[str] = None
        errors: List[str] = []

        if total_files == 0:
            return ExtractionResult(0, 0, None, [])

        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg is not configured.")

        output_dir = Path(self.output_folder) if self.output_folder else None

        for index, input_file in enumerate(self.selected_files, start=1):
            input_path = Path(input_file)
            try:
                destination_dir = output_dir or input_path.parent
                destination_dir.mkdir(parents=True, exist_ok=True)
                output_file = destination_dir / f"{input_path.stem}.{self.output_format}"

                if status_callback:
                    status_callback(index, total_files, input_path.name)

                cmd = [self.ffmpeg_path, "-i", str(input_path), "-vn", "-y"]
                codec = self.AUDIO_CODECS.get(self.output_format)
                if codec:
                    cmd.extend(["-acodec", codec])
                cmd.append(str(output_file))

                kwargs = {}
                if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
                    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    **kwargs,
                )

                if result.returncode == 0:
                    success_count += 1
                    last_output_path = str(output_file)
                else:
                    message = result.stderr or f"FFmpeg exited with code {result.returncode}"
                    errors.append(f"{input_file}: {message}")
                    if error_callback:
                        error_callback(input_file, RuntimeError(message))
            except Exception as exc:  # noqa: BLE001 - broad catch for reporting to the UI
                errors.append(f"{input_file}: {exc}")
                if error_callback:
                    error_callback(input_file, exc)
            finally:
                if progress_callback:
                    progress_callback(index, total_files)

        return ExtractionResult(success_count, total_files, last_output_path, errors)
