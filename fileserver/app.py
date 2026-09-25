"""A small Flask app that serves files from a local directory.

Browse directories and download files. Everything is confined to the
configured root directory; requests that try to escape it (via "..",
symlinks, etc.) are rejected.
"""

from __future__ import annotations

import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, send_from_directory

LAUNCHER_SCRIPT = Path(__file__).resolve().parent.parent / "start_server.py"


def _human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _resolve_within_root(root: Path, subpath: str) -> Path:
    """Resolve subpath against root, rejecting any path traversal attempt."""
    candidate = (root / subpath).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        abort(404)
    return candidate


def create_app(root_dir: str = ".") -> Flask:
    root = Path(root_dir).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    app = Flask(__name__)
    app.config["ROOT_DIR"] = str(root)

    @app.get("/health")
    def health():
        return jsonify(status="ok", root=str(root))

    @app.post("/options")
    def show_options():
        if platform.system() != "Windows":
            return jsonify(
                status="error",
                message="Opening a terminal window is only supported when this service runs on Windows.",
            ), 400

        # Opens a real, visible Command Prompt window on the machine running
        # this service, which then prints start_server.py's --help output.
        subprocess.Popen(
            ["cmd", "/c", "start", "", "cmd", "/k", sys.executable, str(LAUNCHER_SCRIPT), "--help"]
        )
        return jsonify(status="ok", message="Opened a terminal window showing the available options.")

    @app.get("/", defaults={"subpath": ""})
    @app.get("/browse/<path:subpath>")
    def browse(subpath: str):
        target = _resolve_within_root(root, subpath)
        if not target.exists():
            abort(404)

        if target.is_file():
            return send_from_directory(target.parent, target.name, as_attachment=False)

        entries = []
        for entry in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if entry.name.startswith("."):
                continue
            stat = entry.stat()
            entries.append(
                {
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": _human_size(stat.st_size) if entry.is_file() else "",
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "rel_path": str((Path(subpath) / entry.name).as_posix()) if subpath else entry.name,
                }
            )

        parent_rel = str(Path(subpath).parent.as_posix()) if subpath else None
        if parent_rel == ".":
            parent_rel = ""

        return render_template(
            "listing.html",
            current_path=subpath,
            parent_rel=parent_rel,
            entries=entries,
        )

    return app
