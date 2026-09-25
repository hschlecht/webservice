# Local File Server

A small Flask webservice that browses, downloads, and (optionally) accepts
uploads for files in a local directory. It's started by an independent
launcher script, `start_server.py`, which exposes the common options you'd
want when running it locally.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Starting the service

```bash
./start_server.py --directory ~/shared --port 9000
```

### Options

| Option | Default | Description |
| --- | --- | --- |
| `-d, --directory` | `.` | Directory to serve |
| `--host` | `127.0.0.1` | Interface to bind to (`0.0.0.0` to expose on your LAN) |
| `-p, --port` | `8000` | Port to listen on |
| `-w, --workers` | `1` | Number of worker processes (spawns gunicorn); ignored with `--reload` |
| `--reload` | off | Auto-restart on code changes (single-process dev mode) |
| `--log-level` | `info` | `debug`, `info`, `warning`, `error`, `critical` |
| `--show-hidden` | off | Include dotfiles in directory listings |
| `--allow-upload` | off | Enable uploading files into the served directory |
| `--open` | off | Open the server URL in your default browser on startup |

### Examples

```bash
# Quick dev run with auto-reload
./start_server.py -d ./build --reload --log-level debug

# Production-style run with 4 worker processes, opening the browser
./start_server.py -d ./drop --workers 4 --allow-upload --open

# Expose to your LAN
./start_server.py -d ~/public --host 0.0.0.0 --port 8080
```

## Endpoints

- `GET /` and `GET /browse/<path>` — browse directories / download files
- `POST /upload/<path>` — upload a file into `<path>` (only when `--allow-upload` is set)
- `GET /health` — health check, returns `{"status": "ok", "root": "..."}`

All paths are resolved against the configured root directory; requests that
try to escape it (e.g. via `..`) are rejected with a 404.
