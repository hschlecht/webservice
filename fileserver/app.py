"""A small Flask app that serves files from a local directory.

Browse directories, download files, and (optionally) upload new ones.
Everything is confined to the configured root directory; requests that
try to escape it (via "..", symlinks, etc.) are rejected.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    abort,
    jsonify,
    render_template,
    request,
    send_from_directory,
)
from werkzeug.utils import secure_filename


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


def create_app(root_dir: str = ".", show_hidden: bool = False, allow_upload: bool = False) -> Flask:
    root = Path(root_dir).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    app = Flask(__name__)
    app.config["ROOT_DIR"] = str(root)
    app.config["SHOW_HIDDEN"] = show_hidden
    app.config["ALLOW_UPLOAD"] = allow_upload
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1 GiB upload cap

    @app.get("/health")
    def health():
        return jsonify(status="ok", root=str(root))

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
            if not show_hidden and entry.name.startswith("."):
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
            allow_upload=allow_upload,
        )

    @app.post("/upload/", defaults={"subpath": ""})
    @app.post("/upload/<path:subpath>")
    def upload(subpath: str):
        if not allow_upload:
            abort(403)

        target_dir = _resolve_within_root(root, subpath)
        if not target_dir.is_dir():
            abort(404)

        uploaded = request.files.get("file")
        if uploaded is None or uploaded.filename == "":
            abort(400, description="No file provided")

        filename = secure_filename(uploaded.filename)
        if not filename:
            abort(400, description="Invalid filename")

        uploaded.save(target_dir / filename)
        dest = f"/browse/{subpath}" if subpath else "/"
        return jsonify(status="ok", saved_as=filename), 201, {"Location": dest}

    return app
