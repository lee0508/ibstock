import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "shorts_latest.json"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "shorts_normalized.json"
DB_PATH = PROJECT_ROOT / "data" / "db" / "ibstock.db"
INDEX_PATH = PROJECT_ROOT / "faiss_index" / "index.faiss"
REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "data_scrapper_report.json"


def run_step(name: str, cmd: list[str]) -> tuple[bool, str]:
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True, result.stdout.strip()
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    detail = stderr or stdout or f"exit_code={result.returncode}"
    return False, detail


def check_python_module(module_name: str) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True, f"module '{module_name}' available"
    detail = result.stderr.strip() or result.stdout.strip() or "unknown import error"
    return False, detail


def read_raw_count() -> int:
    if not RAW_PATH.exists():
        return 0
    payload = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    return len(payload.get("items", []))


def read_processed_count() -> int:
    if not PROCESSED_PATH.exists():
        return 0
    payload = json.loads(PROCESSED_PATH.read_text(encoding="utf-8"))
    return len(payload.get("items", []))


def build_report(steps: list[dict]) -> dict:
    report = {
        "generated_at": datetime.now().isoformat(),
        "steps": steps,
        "files": {
            "raw_exists": RAW_PATH.exists(),
            "processed_exists": PROCESSED_PATH.exists(),
            "db_exists": DB_PATH.exists(),
            "index_exists": INDEX_PATH.exists(),
            "raw_count": read_raw_count(),
            "processed_count": read_processed_count(),
        },
    }
    report["ok"] = all(step["ok"] for step in steps) and report["files"]["processed_count"] > 0
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and build demo data pipeline")
    parser.add_argument("--limit", type=int, default=80, help="shorts collection limit")
    args = parser.parse_args()

    steps: list[dict] = []

    faiss_ok, faiss_detail = check_python_module("faiss")
    steps.append({"name": "check_faiss_dependency", "ok": faiss_ok, "detail": faiss_detail})
    print(f"[{'OK' if faiss_ok else 'FAIL'}] check_faiss_dependency")
    if not faiss_ok:
        report = build_report(steps)
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("hint: install dependencies with `pip install -r backend/requirements.txt`")
        print(f"report: {REPORT_PATH}")
        print("RESULT: FAIL")
        return 1

    pipeline = [
        ("collect_shorts", [sys.executable, "-X", "utf8", "scripts/collect_shorts.py", "--limit", str(args.limit)]),
        ("preprocess", [sys.executable, "-X", "utf8", "scripts/preprocess.py"]),
        ("init_db", [sys.executable, "-X", "utf8", "scripts/init_db.py"]),
        ("build_index", [sys.executable, "-X", "utf8", "scripts/build_index.py"]),
        ("preflight", [sys.executable, "-X", "utf8", "scripts/preflight_check.py"]),
    ]

    for name, cmd in pipeline:
        ok, detail = run_step(name, cmd)
        steps.append({"name": name, "ok": ok, "detail": detail})
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {name}")
        if not ok:
            break

    report = build_report(steps)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {REPORT_PATH}")
    print(f"raw_count={report['files']['raw_count']} processed_count={report['files']['processed_count']}")

    if report["ok"]:
        print("RESULT: OK")
        return 0

    print("RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
