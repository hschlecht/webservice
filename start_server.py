#!/usr/bin/env python3
"""Independent launcher for the local file-server webservice.

Usage:
    ./start_server.py [directory] --host HOST --port PORT

Examples:
    ./start_server.py
    ./start_server.py ~/shared --port 9000
    ./start_server.py ./build --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start a local file-server webservice.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to serve.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Hostname/interface to bind to. Use 0.0.0.0 to expose on your LAN.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    from fileserver import create_app

    app = create_app(root_dir=str(root))

    print(f"Serving {root} at http://{args.host}:{args.port}/")
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
