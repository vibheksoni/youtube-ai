"""YTAI FastAPI service."""



import sys

from pathlib import Path



_SDK_DIR = Path(__file__).resolve().parent.parent / "sdk"

if _SDK_DIR.is_dir() and str(_SDK_DIR) not in sys.path:

    sys.path.insert(0, str(_SDK_DIR))
