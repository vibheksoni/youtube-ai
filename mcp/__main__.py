"""Allow running the server with ``python -m mcp``."""



import runpy

from pathlib import Path



runpy.run_path(

    str(Path(__file__).resolve().parent / "server.py"),

    run_name="__main__",

)
