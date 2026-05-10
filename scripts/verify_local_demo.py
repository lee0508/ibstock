import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUERIES = ["대한전선", "JP모건", "원자력"]


def post_json(url: str, payload: dict, timeout: int = 8) -> tuple[bool, dict | str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return True, json.loads(body)
    except Exception as exc:
        return False, str(exc)


def get_json(url: str, timeout: int = 8) -> tuple[bool, dict | str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return True, json.loads(body)
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except Exception as exc:
        return False, str(exc)


def run_verification(base_url: str, queries: list[str]) -> dict:
    result: dict = {
        "verified_at": datetime.now().isoformat(),
        "base_url": base_url,
        "health": {},
        "query_checks": [],
    }

    ok_health, health_data = get_json(f"{base_url}/api/health")
    result["health"] = {
        "ok": ok_health,
        "data": health_data,
    }

    for query in queries:
        ok_query, query_data = post_json(
            f"{base_url}/api/stock/query",
            {"query": query, "limit": 3, "mode": "keyword"},
        )
        item_count = 0
        answer_preview = ""
        if ok_query and isinstance(query_data, dict):
            item_count = len(query_data.get("items") or [])
            answer_preview = str(query_data.get("answer") or "")[:180]
        result["query_checks"].append(
            {
                "query": query,
                "ok": ok_query,
                "item_count": item_count,
                "answer_preview": answer_preview,
                "data": query_data,
            }
        )
    return result


def write_markdown_report(report: dict, out_path: Path) -> None:
    lines = []
    lines.append("# 2026-05-10 로컬실기동및Query검증")
    lines.append("")
    lines.append(f"- 검증시각: `{report['verified_at']}`")
    lines.append(f"- 대상 URL: `{report['base_url']}`")
    lines.append("")
    lines.append("## 1. Health 체크")
    health = report["health"]
    lines.append(f"- 결과: `{'OK' if health.get('ok') else 'FAIL'}`")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(health.get("data"), ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## 2. Query 생성형 응답 체크")
    for row in report["query_checks"]:
        lines.append(f"- 질의: `{row['query']}`")
        lines.append(f"- 결과: `{'OK' if row['ok'] else 'FAIL'}`")
        lines.append(f"- item_count: `{row['item_count']}`")
        if row["answer_preview"]:
            lines.append(f"- answer_preview: `{row['answer_preview']}`")
        lines.append("")
    lines.append("## 3. 원본 응답(JSON)")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify local demo endpoints and write report")
    parser.add_argument("--base-url", default="http://127.0.0.1:8081")
    parser.add_argument("--out", default="2026-05-10_로컬실기동및Query검증.md")
    args = parser.parse_args()

    report = run_verification(args.base_url, DEFAULT_QUERIES)
    out_path = PROJECT_ROOT / args.out
    write_markdown_report(report, out_path)

    if not report["health"].get("ok"):
        print(f"verification report written: {out_path} (health failed)")
        return 1

    query_fail_count = sum(1 for row in report["query_checks"] if not row["ok"])
    if query_fail_count:
        print(f"verification report written: {out_path} ({query_fail_count} query checks failed)")
        return 1

    print(f"verification report written: {out_path} (all checks passed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
