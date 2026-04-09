import importlib.util
import socket
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_docs_portal.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_docs_portal", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def port_is_free(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def test_docs_package_uses_portal_launcher_scripts():
    text = (REPO_ROOT / "docs" / "package.json").read_text(encoding="utf-8")
    assert "run_docs_portal.py dev" in text
    assert "run_docs_portal.py preview" in text


def test_pick_available_port_moves_to_next_free_port():
    module = load_module()

    start_port = None
    for candidate in range(46173, 46273):
        if port_is_free(candidate) and port_is_free(candidate + 1):
            start_port = candidate
            break

    assert start_port is not None

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", start_port))
        resolved = module.pick_available_port(start_port, host="127.0.0.1", max_tries=4)
    finally:
        sock.close()

    assert resolved == start_port + 1
