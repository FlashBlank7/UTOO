#!/usr/bin/env python3
"""Boot the staged Lilies module behind UTOO and verify the public routes."""

from __future__ import annotations

import base64
import http.cookiejar
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


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def fetch(
    url: str,
    timeout: float = 3,
    opener: urllib.request.OpenerDirector | None = None,
) -> tuple[int, bytes, str]:
    open_request = opener.open if opener else urllib.request.urlopen
    with open_request(url, timeout=timeout) as response:
        return response.status, response.read(), response.geturl()


def request_result(
    request: urllib.request.Request | str,
    timeout: float = 5,
    opener: urllib.request.OpenerDirector | None = None,
) -> tuple[int, bytes, str, object]:
    open_request = opener.open if opener else urllib.request.urlopen
    try:
        with open_request(request, timeout=timeout) as response:
            return response.status, response.read(), response.geturl(), response.headers
    except urllib.error.HTTPError as response:
        return response.code, response.read(), response.geturl(), response.headers


def post_json(
    url: str,
    payload: dict[str, str],
    timeout: float = 5,
    opener: urllib.request.OpenerDirector | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, object]]:
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    status, body, _, _ = request_result(request, timeout=timeout, opener=opener)
    if status >= 400:
        raise RuntimeError(f"POST {url} returned {status}: {body.decode(errors='replace')}")
    return status, json.loads(body) if body else {}


def wait_for(
    url: str,
    timeout_seconds: int = 45,
    opener: urllib.request.OpenerDirector | None = None,
) -> tuple[int, bytes, str]:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            status, body, final_url = fetch(url, opener=opener)
            if status == 200:
                return status, body, final_url
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def assert_denied(
    base_url: str,
    opener: urllib.request.OpenerDirector,
    label: str,
) -> None:
    status, _, _, headers = request_result(f"{base_url}/lilies", opener=opener)
    location = headers.get("Location")
    if status != 303 or location != "/login?next=%2Flilies":
        raise RuntimeError(
            f"{label} Lilies page should redirect to login; got {status} {location!r}"
        )

    status, body, _, _ = request_result(
        f"{base_url}/api/platform/health",
        opener=opener,
    )
    if status != 401:
        raise RuntimeError(
            f"{label} Lilies API should return 401; got {status}: {body.decode(errors='replace')}"
        )

    write_request = urllib.request.Request(
        f"{base_url}/lilies",
        data=b"",
        method="POST",
    )
    status, _, _, _ = request_result(write_request, opener=opener)
    if status != 401:
        raise RuntimeError(f"{label} Lilies write should return 401; got {status}")


def jwt_payload(token: str) -> dict[str, object]:
    encoded = token.split(".")[1]
    padded = encoded + "=" * (-len(encoded) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


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

            subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from alembic.config import Config; "
                        "from alembic import command; "
                        "command.upgrade(Config('alembic.ini'), 'head')"
                    ),
                ],
                cwd=BACKEND,
                env=env,
                check=True,
                stdout=logs["utoo"],
                stderr=subprocess.STDOUT,
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
            base_url = f"http://127.0.0.1:{utoo_port}"
            _, module_health, _ = wait_for(f"{base_url}/health/lilies")
            if json.loads(module_health).get("status") != "ok":
                raise RuntimeError("Public Lilies readiness response is not OK")

            anonymous_opener = urllib.request.build_opener(NoRedirectHandler())
            assert_denied(base_url, anonymous_opener, "Anonymous")

            cookie_jar = http.cookiejar.CookieJar()
            authenticated_opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(cookie_jar)
            )
            authenticated_no_redirect_opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(cookie_jar),
                NoRedirectHandler(),
            )
            register_status, tokens = post_json(
                f"{base_url}/api/v1/auth/register",
                {
                    "activation_code": "UTOO-ADMIN",
                    "username": "lilies-smoke",
                    "password": "lilies-smoke-password",
                    "department": "Smoke test",
                    "school_input": "枝江大学",
                },
                opener=authenticated_opener,
            )
            if register_status != 201:
                raise RuntimeError(f"Smoke user registration returned {register_status}")
            access_token = tokens.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise RuntimeError("Smoke user registration did not return an access token")

            session_cookie = next(
                (cookie for cookie in cookie_jar if cookie.name == "utoo_lilies_session"),
                None,
            )
            if not session_cookie or not session_cookie.has_nonstandard_attr("HttpOnly"):
                raise RuntimeError("Login did not issue an HttpOnly Lilies session cookie")
            if jwt_payload(session_cookie.value).get("type") != "lilies_session":
                raise RuntimeError("Lilies cookie did not use the isolated session token type")

            session_status, _ = post_json(
                f"{base_url}/api/v1/auth/lilies-session",
                {},
                opener=authenticated_opener,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if session_status != 204:
                raise RuntimeError(f"Lilies session refresh returned {session_status}")

            _, page, final_url = wait_for(
                f"{base_url}/lilies",
                opener=authenticated_opener,
            )
            if b"/lilies/_next/" not in page:
                raise RuntimeError("Lilies page does not use the /lilies asset base path")
            if not final_url.rstrip("/").endswith("/lilies"):
                raise RuntimeError(f"Lilies public route escaped its module path: {final_url}")

            _, proxy_health, _ = wait_for(
                f"{base_url}/api/platform/health",
                opener=authenticated_opener,
            )
            if json.loads(proxy_health).get("status") != "ok":
                raise RuntimeError("Lilies API proxy health response is not OK")

            _, application = post_json(
                f"{base_url}/api/platform/api/v1/applications",
                {
                    "name": "UTOO Lilies smoke",
                    "description": "Temporary module integration check",
                    "requirement": "Create a deterministic smoke-test workflow",
                    "mode": "workflow",
                },
                opener=authenticated_opener,
            )
            application_id = application.get("id")
            if not isinstance(application_id, str) or not application_id:
                raise RuntimeError("Lilies application creation did not return an ID")
            wait_for(
                f"{base_url}/lilies/applications/{application_id}/session",
                opener=authenticated_opener,
            )

            session_token = next(
                cookie.value
                for cookie in cookie_jar
                if cookie.name == "utoo_lilies_session"
            )
            main_api_request = urllib.request.Request(
                f"{base_url}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {session_token}"},
            )
            status, _, _, _ = request_result(main_api_request)
            if status != 401:
                raise RuntimeError("Lilies session token was accepted by the main UTOO API")

            logout_request = urllib.request.Request(
                f"{base_url}/api/v1/auth/lilies-session",
                method="DELETE",
            )
            status, _, _, _ = request_result(logout_request, opener=authenticated_opener)
            if status != 204:
                raise RuntimeError(f"Lilies logout returned {status}")
            assert_denied(base_url, authenticated_no_redirect_opener, "Logged-out")

            print(
                "Lilies module smoke passed: "
                f"{base_url}/lilies is authenticated; API proxy and application route work"
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
