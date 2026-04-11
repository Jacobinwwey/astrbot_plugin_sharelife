#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import socket
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
PRIVATE_DOCS_SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_local_private_docs.py"


def npm_command() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def vitepress_command() -> Path:
    binary_name = "vitepress.cmd" if os.name == "nt" else "vitepress"
    return DOCS_ROOT / "node_modules" / ".bin" / binary_name


def is_port_available(port: int, *, host: str = "127.0.0.1") -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow quick restart after stopping a previous docs process where
    # local connections may still keep the port in TIME_WAIT.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, int(port)))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def pick_available_port(start_port: int, *, host: str = "127.0.0.1", max_tries: int = 50) -> int:
    port = int(start_port)
    for _ in range(max_tries):
        if is_port_available(port, host=host):
            return port
        port += 1
    raise RuntimeError(f"no free docs port found starting from {start_port}")


def run_prepare() -> None:
    script_name = "docs:prepare:with-private" if PRIVATE_DOCS_SYNC_SCRIPT.exists() else "docs:prepare"
    subprocess.run(
        [npm_command(), "--prefix", str(DOCS_ROOT), "run", script_name],
        check=True,
    )


def run_build() -> None:
    script_name = "docs:build:with-private" if PRIVATE_DOCS_SYNC_SCRIPT.exists() else "docs:build"
    subprocess.run(
        [npm_command(), "--prefix", str(DOCS_ROOT), "run", script_name],
        check=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Sharelife docs with deterministic port fallback.")
    parser.add_argument("mode", choices=("dev", "preview"))
    parser.add_argument("--host", default=os.getenv("SHARELIFE_DOCS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("SHARELIFE_DOCS_PORT", "4173")))
    parser.add_argument("--max-port-tries", type=int, default=int(os.getenv("SHARELIFE_DOCS_MAX_PORT_TRIES", "50")))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, passthrough = parser.parse_known_args(argv)

    if args.mode == "preview":
        run_build()
    else:
        run_prepare()

    resolved_port = pick_available_port(args.port, host=args.host, max_tries=args.max_port_tries)
    vitepress_bin = vitepress_command()
    if not vitepress_bin.exists():
        raise SystemExit(f"vitepress binary not found: {vitepress_bin}")

    print(
        f"[docs-portal] mode={args.mode} requested_port={args.port} resolved_port={resolved_port} "
        f"url=http://{args.host}:{resolved_port}/astrbot_plugin_sharelife/",
        flush=True,
    )

    command = [
        str(vitepress_bin),
        args.mode,
        ".",
        "--host",
        args.host,
        "--port",
        str(resolved_port),
        *passthrough,
    ]
    completed = subprocess.run(command, cwd=DOCS_ROOT)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
