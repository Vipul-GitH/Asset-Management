"""Single-command launcher for the Asset Management System."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
SSL_CERTIFICATE = ROOT_DIR / "certs" / "fullchain.pem"
SSL_PRIVATE_KEY = ROOT_DIR / "certs" / "privkey.pem"


def bootstrap() -> None:
    """Prepare a fresh checkout so `py app.py` is the only setup command."""
    if not (ROOT_DIR / ".env").is_file() and (ROOT_DIR / ".env.example").is_file():
        shutil.copyfile(ROOT_DIR / ".env.example", ROOT_DIR / ".env")
        print("Created .env from .env.example")

    if VENV_PYTHON.is_file():
        return

    print("Creating Python environment...")
    subprocess.check_call([sys.executable, "-m", "venv", str(ROOT_DIR / ".venv")])
    print("Installing project dependencies...")
    subprocess.check_call(
        [
            str(VENV_PYTHON),
            "-m",
            "pip",
            "install",
            "-r",
            str(BACKEND_DIR / "requirements.txt"),
        ]
    )
    print("Applying database migrations...")
    subprocess.check_call(
        [str(VENV_PYTHON), "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
    )


def main() -> int:
    try:
        bootstrap()
    except subprocess.CalledProcessError as exc:
        print(f"Project setup failed (exit code {exc.returncode}).")
        return exc.returncode or 1

    if Path(sys.executable).resolve() != VENV_PYTHON.resolve():
        return subprocess.call([str(VENV_PYTHON), str(Path(__file__).resolve())])

    missing = [
        path.relative_to(ROOT_DIR)
        for path in (SSL_CERTIFICATE, SSL_PRIVATE_KEY)
        if not path.is_file()
    ]
    if missing:
        print("Cannot start HTTPS server. Missing: " + ", ".join(map(str, missing)))
        return 1

    sys.path.insert(0, str(BACKEND_DIR))
    os.chdir(BACKEND_DIR)

    import uvicorn

    url = "https://labmate.bhasinpathlabs.com:4676"
    print(f"Starting DBL AssetHub at {url}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=4676,
        ssl_certfile=str(SSL_CERTIFICATE),
        ssl_keyfile=str(SSL_PRIVATE_KEY),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
