#!/usr/bin/env python3
"""Boot the staged Lilies module behind UTOO and verify the public routes."""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
LILIES = BACKEND / "lilies"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def fetch(url: str, timeout: float = 3) -> tuple[int, bytes, str]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.status, response.read(), response.geturl()


def post_json(url: str, payload: dict[str, str], timeout: float = 5) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def wait_for(url: str, timeout_seconds: int = 45) -> tuple[int, bytes, str]:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            status, body, final_url = fetch(url)
            if status == 200:
                return status, body, final_url
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def stop(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def main() -> int:
    required = [
        LILIES / "backend" / "agent_platform" / "api.py",
        LILIES / "frontend" / "server.js",
        LILIES / "frontend" / ".next" / "static",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"Lilies module is not staged: {', '.join(missing)}")

    bundled_node = LILIES / "runtime" / "node"
    node = str(bundled_node) if bundled_node.is_file() else shutil.which("node")
    if not node:
        raise RuntimeError("Node.js runtime is unavailable")

    api_port, frontend_port, utoo_port = free_port(), free_port(), free_port()
    processes: list[subprocess.Popen[bytes]] = []

    with tempfile.TemporaryDirectory(prefix="utoo-lilies-smoke-") as temp_dir:
        temp = Path(temp_dir)
        log_paths = {
            "api": temp / "lilies-api.log",
            "frontend": temp / "lilies-frontend.log",
            "utoo": temp / "utoo.log",
        }
        logs = {name: path.open("wb") for name, path in log_paths.items()}
        try:
            env = os.environ.copy()
            env.update(
                {
                    "PYTHONPATH": os.pathsep.join(
                        [str(LILIES / "backend"), str(BACKEND), env.get("PYTHONPATH", "")]
                    ),
                    "DATA_DIR": str(temp / "lilies-data"),
                    "WORKSPACE_ROOT": str(temp / "lilies-workspaces"),
                    "API_TOKEN": "utoo-lilies-smoke-token",
                    "MODEL_EGRESS_ENABLED": "false",
                    "AGENT_PLATFORM_URL": f"http://127.0.0.1:{api_port}",
                    "LILIES_FRONTEND_URL": f"http://127.0.0.1:{frontend_port}",
                    "DATABASE_URL": f"sqlite+aiosqlite:///{temp / 'utoo.db'}",
                    "SECRET_KEY": "utoo-lilies-smoke-secret",
                    "ALLOWED_ORIGINS": f"http://127.0.0.1:{utoo_port}",
                }
            )

            processes.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "agent_platform.api:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(api_port),
                    ],
                    cwd=LILIES / "backend",
                    env=env,
                    stdout=logs["api"],
                    stderr=subprocess.STDOUT,
                )
            )
            _, api_body, _ = wait_for(f"http://127.0.0.1:{api_port}/health")
            if json.loads(api_body).get("status") != "ok":
                raise RuntimeError("Lilies API health response is not OK")

            frontend_env = env.copy()
            frontend_env.update({"HOSTNAME": "127.0.0.1", "PORT": str(frontend_port)})
            processes.append(
                subprocess.Popen(
                    [node, "server.js"],
                    cwd=LILIES / "frontend",
                    env=frontend_env,
                    stdout=logs["frontend"],
                    stderr=subprocess.STDOUT,
                )
            )
            wait_for(f"http://127.0.0.1:{frontend_port}/lilies")

            processes.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "app.main:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(utoo_port),
                    ],
                    cwd=BACKEND,
                    env=env,
                    stdout=logs["utoo"],
                    stderr=subprocess.STDOUT,
                )
            )
            wait_for(f"http://127.0.0.1:{utoo_port}/health")
            _, page, final_url = wait_for(f"http://127.0.0.1:{utoo_port}/lilies")
            if b"/lilies/_next/" not in page:
                raise RuntimeError("Lilies page does not use the /lilies asset base path")
            if not final_url.rstrip("/").endswith("/lilies"):
                raise RuntimeError(f"Lilies public route escaped its module path: {final_url}")

            _, proxy_health, _ = wait_for(
                f"http://127.0.0.1:{utoo_port}/api/platform/health"
            )
            if json.loads(proxy_health).get("status") != "ok":
                raise RuntimeError("Lilies API proxy health response is not OK")

            application = post_json(
                f"http://127.0.0.1:{utoo_port}/api/platform/api/v1/applications",
                {
                    "name": "UTOO Lilies smoke",
                    "description": "Temporary module integration check",
                    "requirement": "Create a deterministic smoke-test workflow",
                    "mode": "workflow",
                },
            )
            application_id = application.get("id")
            if not isinstance(application_id, str) or not application_id:
                raise RuntimeError("Lilies application creation did not return an ID")
            wait_for(
                f"http://127.0.0.1:{utoo_port}/lilies/applications/"
                f"{application_id}/session"
            )

            print(
                "Lilies module smoke passed: "
                f"http://127.0.0.1:{utoo_port}/lilies, API proxy, and application route"
            )
        except Exception:
            for process in reversed(processes):
                stop(process)
            for stream in logs.values():
                stream.close()
            for name, path in log_paths.items():
                if path.exists():
                    print(f"--- {name} log ---", file=sys.stderr)
                    print(path.read_text(encoding="utf-8", errors="replace"), file=sys.stderr)
            raise
        else:
            for process in reversed(processes):
                stop(process)
            for stream in logs.values():
                stream.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
