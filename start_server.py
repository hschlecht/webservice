#!/usr/bin/env python3
"""Independent launcher for the local file-server webservice.

Examples:
    ./start_server.py --directory ~/shared --port 9000
    ./start_server.py -d ./build --reload --log-level debug
    ./start_server.py -d ./drop --workers 4 --allow-upload --open
"""

from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from pathlib import Path

LOG_LEVELS = ["debug", "info", "warning", "error", "critical"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start a local file-server webservice.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-d", "--directory",
        default=".",
        help="Directory to serve.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Interface to bind to. Use 0.0.0.0 to expose on your LAN.",
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Port to listen on.",
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=1,
        help="Number of worker processes (uses gunicorn). Ignored with --reload.",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Auto-restart the server when source files change (single-process dev mode).",
    )
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS,
        default="info",
        help="Logging verbosity.",
    )
    parser.add_argument(
        "--show-hidden",
        action="store_true",
        help="Include dotfiles/dot-directories in directory listings.",
    )
    parser.add_argument(
        "--allow-upload",
        action="store_true",
        help="Enable uploading files into the served directory.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the server URL in your default browser once it starts.",
    )

    args = parser.parse_args(argv)

    if args.reload and args.workers != 1:
        parser.error("--reload cannot be combined with --workers > 1 (dev mode is single-process)")
    if args.workers < 1:
        parser.error("--workers must be at least 1")

    return args


def run_dev_server(args: argparse.Namespace, root: Path) -> None:
    from fileserver import create_app

    app = create_app(
        root_dir=str(root),
        show_hidden=args.show_hidden,
        allow_upload=args.allow_upload,
    )
    app.run(
        host=args.host,
        port=args.port,
        debug=args.log_level == "debug",
        use_reloader=args.reload,
        threaded=True,
    )


def run_gunicorn(args: argparse.Namespace, root: Path) -> None:
    import subprocess

    env = os.environ.copy()
    env["FILESERVER_ROOT"] = str(root)
    env["FILESERVER_SHOW_HIDDEN"] = "1" if args.show_hidden else "0"
    env["FILESERVER_ALLOW_UPLOAD"] = "1" if args.allow_upload else "0"

    cmd = [
        sys.executable, "-m", "gunicorn",
        "--bind", f"{args.host}:{args.port}",
        "--workers", str(args.workers),
        "--log-level", args.log_level,
        "fileserver.wsgi:app",
    ]
    result = subprocess.run(cmd, env=env)
    sys.exit(result.returncode)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    url = f"http://{args.host}:{args.port}/"
    print(f"Serving {root} at {url}")
    if args.open:
        import threading

        threading.Timer(1.0, webbrowser.open, args=[url]).start()

    if args.reload or args.workers == 1:
        run_dev_server(args, root)
    else:
        run_gunicorn(args, root)


if __name__ == "__main__":
    main()
