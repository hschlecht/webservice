"""WSGI entrypoint used by gunicorn for multi-worker runs.

Configuration is passed via environment variables by start_server.py,
since gunicorn imports this module fresh in each worker process.
"""

import os

from .app import create_app

app = create_app(
    root_dir=os.environ.get("FILESERVER_ROOT", "."),
    show_hidden=os.environ.get("FILESERVER_SHOW_HIDDEN") == "1",
    allow_upload=os.environ.get("FILESERVER_ALLOW_UPLOAD") == "1",
)
