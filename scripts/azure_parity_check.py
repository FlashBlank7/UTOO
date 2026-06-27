#!/usr/bin/env python3
"""Validate the Azure App Service runtime path locally/inside CI.

This script intentionally checks the production shape, not the Docker Compose
developer shape:

- SQLite database URL like Azure free/small App Service.
- Full Alembic migration chain from an empty database.
- FastAPI import through the same backend package.
- Gunicorn + uvicorn worker health check.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
STATIC_INDEX = BACKEND / "app" / "static" / "index.html"
EXPECTED_MIN_SCHOOLS = 51
EXPECTED_MIN_BOARDS = 357
EXPECTED_ALEMBIC_VERSION = "0009"


def run(cmd: list[str], *, env: dict[str, str], cwd: Path = BACKEND, timeout: int = 120) -> None:
    print(f"+ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout, check=True)


def alembic_upgrade(env: dict[str, str], revision: str = "head") -> None:
    code = """
import os
from alembic.config import Config
from alembic import command
cfg = Config("alembic.ini")
command.upgrade(cfg, os.environ["ALEMBIC_TARGET_REVISION"])
"""
    command_env = env.copy()
    command_env["ALEMBIC_TARGET_REVISION"] = revision
    run([sys.executable, "-c", code], env=command_env, timeout=180)


def create_partial_0008_residue(db_path: Path) -> None:
    """Simulate a failed SQLite 0008 run that left DDL behind before versioning.

    SQLite DDL is not fully transactional under Alembic. Azure may therefore
    retain newly created tables from a failed startup migration while
    alembic_version still points at 0007.
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            create table if not exists schools (
                id integer primary key,
                slug varchar(120) not null unique,
                name_zh varchar(200) not null,
                name_en varchar(200) not null,
                name_ja varchar(200) not null,
                country varchar(50) not null default 'Japan',
                kind varchar(30) not null default 'real',
                rank_source varchar(120),
                rank_label varchar(30),
                rank_order integer,
                theme varchar(40) not null default 'standard',
                is_active boolean not null default 1,
                created_at datetime not null
            )
            """
        )
        conn.execute(
            """
            create table if not exists school_aliases (
                id integer primary key,
                school_id integer not null,
                alias varchar(200) not null,
                alias_normalized varchar(200) not null unique,
                locale varchar(20)
            )
            """
        )
        conn.execute(
            """
            create table if not exists boards (
                id integer primary key,
                school_id integer not null,
                parent_id integer,
                slug varchar(120) not null,
                name varchar(80) not null,
                description text,
                status varchar(20) not null default 'pending',
                sort_order integer not null default 0,
                created_by integer,
                created_at datetime not null,
                updated_at datetime not null
            )
            """
        )


def assert_sqlite_seed(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        version = conn.execute("select version_num from alembic_version").fetchone()
        schools = conn.execute("select count(*) from schools").fetchone()[0]
        boards = conn.execute("select count(*) from boards").fetchone()[0]
        public_school = conn.execute(
            "select kind from schools where slug = 'zhijiang-university'"
        ).fetchone()

    if version != (EXPECTED_ALEMBIC_VERSION,):
        raise RuntimeError(f"Unexpected Alembic version: {version!r}")
    if schools < EXPECTED_MIN_SCHOOLS:
        raise RuntimeError(f"Expected at least {EXPECTED_MIN_SCHOOLS} schools, found {schools}")
    if boards < EXPECTED_MIN_BOARDS:
        raise RuntimeError(f"Expected at least {EXPECTED_MIN_BOARDS} boards, found {boards}")
    if public_school != ("virtual_public",):
        raise RuntimeError("zhijiang-university virtual public school seed is missing")

    print(f"SQLite seed OK: version={version[0]} schools={schools} boards={boards}")


def wait_for_health(port: int, timeout_seconds: int = 30) -> None:
    deadline = time.time() + timeout_seconds
    url = f"http://127.0.0.1:{port}/health"
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                body = response.read().decode("utf-8")
                if response.status == 200 and body.strip() == '{"status":"ok"}':
                    print(f"Health OK: {url}")
                    return
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"Health check did not pass for {url}: {last_error}")


def boot_gunicorn(env: dict[str, str], port: int) -> None:
    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "-w",
        "1",
        "-k",
        "uvicorn.workers.UvicornWorker",
        "-b",
        f"127.0.0.1:{port}",
        "--timeout",
        "60",
        "app.main:app",
    ]
    print(f"+ {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        cwd=BACKEND,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_health(port)
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            output, _ = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            output, _ = proc.communicate(timeout=10)
        print(output or "", end="")
        if proc.returncode not in (0, -signal.SIGTERM):
            raise RuntimeError(f"Gunicorn exited unexpectedly with code {proc.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Azure App Service runtime parity")
    parser.add_argument("--require-static", action="store_true", help="Fail if backend/app/static/index.html is missing")
    parser.add_argument("--skip-server", action="store_true", help="Only check compile + SQLite migrations")
    parser.add_argument("--port", type=int, default=8123)
    args = parser.parse_args()

    if args.require_static and not STATIC_INDEX.is_file():
        raise RuntimeError("frontend build is missing from backend/app/static/index.html")

    with tempfile.TemporaryDirectory(prefix="utoo-azure-parity-") as tmpdir:
        db_path = Path(tmpdir) / "utoo.db"
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
        env["SECRET_KEY"] = env.get("SECRET_KEY", "azure-parity-test-secret")
        env["ALLOWED_ORIGINS"] = "http://127.0.0.1"
        env["PYTHONPATH"] = str(BACKEND)

        run([sys.executable, "-m", "compileall", "app", "alembic"], env=env)
        alembic_upgrade(env)
        assert_sqlite_seed(db_path)
        if not args.skip_server:
            if not shutil.which("gunicorn"):
                raise RuntimeError("gunicorn is not installed; run pip install -r backend/requirements.txt")
            boot_gunicorn(env, args.port)

        partial_db_path = Path(tmpdir) / "utoo-partial-0008.db"
        partial_env = env.copy()
        partial_env["DATABASE_URL"] = f"sqlite+aiosqlite:///{partial_db_path}"
        alembic_upgrade(partial_env, "0007")
        create_partial_0008_residue(partial_db_path)
        alembic_upgrade(partial_env)
        assert_sqlite_seed(partial_db_path)

    print("Azure parity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
