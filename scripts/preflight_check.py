import argparse
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "db" / "ibstock.db"
INDEX_PATH = PROJECT_ROOT / "faiss_index" / "index.faiss"
META_PATH = PROJECT_ROOT / "faiss_index" / "metadata.json"
BUILD_INFO_PATH = PROJECT_ROOT / "faiss_index" / "build_info.json"
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "shorts_latest.json"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "shorts_normalized.json"


def check_file(path: Path, label: str) -> tuple[bool, str]:
    if path.exists() and path.is_file():
        return True, f"PASS {label}: {path}"
    return False, f"FAIL {label}: missing ({path})"


def check_db_rows(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"FAIL DB rows: database not found ({path})"
    try:
        with sqlite3.connect(path) as conn:
            row = conn.execute("SELECT COUNT(*) FROM shorts_videos").fetchone()
            count = int(row[0]) if row else 0
            if count > 0:
                return True, f"PASS DB rows: shorts_videos={count}"
            return False, "FAIL DB rows: shorts_videos is empty"
    except Exception as exc:
        return False, f"FAIL DB rows: {exc}"


def check_ollama(host: str) -> tuple[bool, str]:
    url = f"{host.rstrip('/')}/api/tags"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
            models = payload.get("models", [])
            return True, f"PASS Ollama: reachable ({len(models)} models)"
    except urllib.error.URLError as exc:
        return False, f"WARN Ollama: unreachable ({exc})"
    except Exception as exc:
        return False, f"WARN Ollama: check failed ({exc})"


def main() -> int:
    parser = argparse.ArgumentParser(description="IBStock local demo preflight checks")
    parser.add_argument("--ollama-host", default="http://127.0.0.1:11434")
    parser.add_argument("--strict-ollama", action="store_true")
    args = parser.parse_args()

    checks = [
        check_file(RAW_PATH, "raw data"),
        check_file(PROCESSED_PATH, "processed data"),
        check_file(DB_PATH, "sqlite db"),
        check_file(INDEX_PATH, "faiss index"),
        check_file(META_PATH, "faiss metadata"),
        check_file(BUILD_INFO_PATH, "faiss build info"),
        check_db_rows(DB_PATH),
    ]

    all_required_ok = True
    for ok, message in checks:
        print(message)
        if not ok:
            all_required_ok = False

    ollama_ok, ollama_message = check_ollama(args.ollama_host)
    print(ollama_message)

    if not all_required_ok:
        print("RESULT: FAIL (required checks)")
        return 1

    if args.strict_ollama and not ollama_ok:
        print("RESULT: FAIL (strict ollama mode)")
        return 1

    if ollama_ok:
        print("RESULT: OK")
    else:
        print("RESULT: OK (ollama warning)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
