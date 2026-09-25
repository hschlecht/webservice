# Local File Server

A small Flask webservice that browses and downloads files from a local
directory. It's started by an independent launcher script, `start_server.py`,
which takes just the directory to serve, a hostname, and a port.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Starting the service

```bash
./start_server.py [directory] --host HOST --port PORT
```

| Argument | Default | Description |
| --- | --- | --- |
| `directory` | `.` | Directory to serve |
| `--host` | `127.0.0.1` | Hostname/interface to bind to (`0.0.0.0` to expose on your LAN) |
| `--port` | `8000` | Port to listen on |

### Examples

```bash
# Serve the current directory on the default host/port
./start_server.py

# Serve a specific directory on a chosen port
./start_server.py ~/shared --port 9000

# Expose to your LAN
./start_server.py ~/public --host 0.0.0.0 --port 8080
```

## Endpoints

- `GET /` and `GET /browse/<path>` — browse directories / download files
- `GET /health` — health check, returns `{"status": "ok", "root": "..."}`
- `POST /options` — **Windows only.** Opens a real Command Prompt window on
  the machine running the service and runs `start_server.py --help` in it,
  so you can see the launcher's options. There's a "Show start_server.py
  options" button at the bottom of the directory listing that triggers it.
  On any other OS it returns a 400 error instead of opening a window.

All paths are resolved against the configured root directory; requests that
try to escape it (e.g. via `..`) are rejected with a 404.
