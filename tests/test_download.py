"""FFmpeg resolution tests using real executable packages and paths."""



import os

import shutil

import subprocess

import sys

from pathlib import Path



import pytest



sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))



from youtube_ai.download import DownloadError, _find_ffmpeg





def _assert_runs(path: str) -> None:

    result = subprocess.run([path, "-version"], capture_output=True, text=True, timeout=30)

    assert result.returncode == 0

    assert result.stdout.lower().startswith("ffmpeg version")





def test_bundled_ffmpeg_resolves_without_path(monkeypatch):

    monkeypatch.delenv("YTAI_FFMPEG_PATH", raising=False)

    monkeypatch.setenv("PATH", "")



    path = _find_ffmpeg()



    assert path is not None

    assert Path(path).is_file()

    _assert_runs(path)





def test_system_ffmpeg_wins_when_available(monkeypatch):

    system_path = shutil.which("ffmpeg")

    if not system_path:

        pytest.skip("system ffmpeg is not installed")

    monkeypatch.delenv("YTAI_FFMPEG_PATH", raising=False)



    assert _find_ffmpeg() == system_path





def test_explicit_ffmpeg_path_wins(monkeypatch):

    bundled_path = _find_ffmpeg()

    assert bundled_path is not None

    assert _find_ffmpeg(bundled_path) == bundled_path

    monkeypatch.setenv("YTAI_FFMPEG_PATH", bundled_path)



    assert _find_ffmpeg() == bundled_path





def test_invalid_explicit_ffmpeg_path_fails_clearly(monkeypatch):

    monkeypatch.setenv("YTAI_FFMPEG_PATH", os.path.join("missing", "ffmpeg"))



    with pytest.raises(DownloadError, match="YTAI_FFMPEG_PATH"):

        _find_ffmpeg()
