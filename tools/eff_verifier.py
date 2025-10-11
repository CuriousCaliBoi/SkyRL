#!/usr/bin/env python3
"""
Lightweight EFF verifier: computes PR metrics and an NSS-style score.

Outputs:
- Appends one JSON line to metrics/nss.jsonl (path configurable via --out)
- Optionally posts a PR comment with a human summary (requires GITHUB_TOKEN)

Notes:
- Normalization uses EFF targets (section: North-Star Score) with simple caps:
  * Higher-is-better: score = min(1, value/target)
  * Lower-is-better:  score = min(1, target/value) (value>0)
- If a metric is missing, it’s excluded and weights renormalize for partial_nss.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    yaml = None  # fallback to defaults if PyYAML not available


def run(cmd: list[str], cwd: Optional[str] = None) -> str:
    out = subprocess.check_output(cmd, cwd=cwd)
    return out.decode("utf-8", errors="replace").strip()


def parse_numstat(base: str, head: str) -> Tuple[int, int, Dict[str, Tuple[int, int]]]:
    """Return added_sum, deleted_sum, and per-file (added, deleted)."""
    args = ["git", "diff", "--numstat", f"{base}...{head}"]
    text = run(args)
    added = deleted = 0
    per_file: Dict[str, Tuple[int, int]] = {}
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, d, path = parts[0], parts[1], parts[2]
        try:
            a_i = int(a) if a.isdigit() else 0
            d_i = int(d) if d.isdigit() else 0
        except ValueError:
            a_i = d_i = 0
        added += a_i
        deleted += d_i
        per_file[path] = (a_i, d_i)
    return added, deleted, per_file


def list_changed_files(base: str, head: str) -> list[str]:
    text = run(["git", "diff", "--name-only", f"{base}...{head}"])
    return [ln for ln in text.splitlines() if ln.strip()]


def is_doc(path: str) -> bool:
    p = path.lower()
    return (
        p.startswith("docs/")
        or p.endswith(".md")
        or p.endswith(".rst")
        or p.endswith(".mdx")
    )


def is_test(path: str) -> bool:
    base = os.path.basename(path)
    p = path.replace("\\", "/").lower()
    return (
        "/tests/" in f"/{p}" or base.startswith("test_") or base.endswith("_test.py")
    )


def load_eff_weights(path: str = "eff.config.yaml") -> Dict[str, float]:
    # Defaults from AGENTS.md if config or YAML not available
    defaults = {
        "merge_velocity": 0.30,
        "defect_recovery": 0.25,
        "subtraction_ratio": 0.15,
        "doc_test_depth": 0.15,
        "cycle_time": 0.15,
    }
    try:
        if yaml and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return (
                data.get("scoring", {})
                .get("weights", defaults)
            )
    except Exception:
        pass
    return defaults


def github_api(url: str, token: str) -> Dict[str, Any]:
    import urllib.request

    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req, timeout=15) as resp:  # nosec - Actions context
        return json.loads(resp.read().decode("utf-8"))


def post_github_comment(repo: str, pr_number: int, body: str, token: str, api_base: str) -> None:
    import urllib.request

    url = f"{api_base}/repos/{repo}/issues/{pr_number}/comments"
    data = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:  # nosec - Actions context
        _ = resp.read()


def compute_cycle_time_hours(repo: str, pr_number: int, token: str, api_base: str) -> Optional[float]:
    pr = github_api(f"{api_base}/repos/{repo}/pulls/{pr_number}", token)
    created = pr.get("created_at")
    merged = pr.get("merged_at")
    closed = pr.get("closed_at")
    if not created:
        return None
    def _parse(ts: str) -> dt.datetime:
        return dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    t0 = _parse(created)
    tn = _parse(merged) if merged else (_parse(closed) if closed else dt.datetime.now(dt.timezone.utc))
    return max(0.0, (tn - t0).total_seconds() / 3600.0)


def merged_prs_last_7d(repo: str, token: str, api_base: str) -> Optional[int]:
    since = (dt.datetime.utcnow() - dt.timedelta(days=7)).strftime("%Y-%m-%d")
    q = f"is:pr+repo:{repo}+is:merged+merged:>={since}"
    url = f"{api_base}/search/issues?q={q}"
    try:
        data = github_api(url, token)
        return int(data.get("total_count", 0))
    except Exception:
        return None


def clamp01(x: Optional[float]) -> Optional[float]:
    if x is None:
        return None
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return x


def main() -> int:
    p = argparse.ArgumentParser(description="EFF verifier: compute NSS-style metrics for PRs")
    p.add_argument("--base", default=os.environ.get("BASE_REF", "origin/HEAD"), help="Base ref to diff against (git ref)")
    p.add_argument("--head", default="HEAD", help="Head ref (git ref)")
    p.add_argument("--out", default="metrics/nss.jsonl", help="Path to metrics JSONL output")
    p.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"), help="owner/repo for GitHub API")
    p.add_argument("--pr-number", type=int, default=int(os.environ.get("PR_NUMBER", "0") or 0))
    p.add_argument("--post-comment", action="store_true", help="Post a PR comment with summary if token present")
    args = p.parse_args()

    base, head = args.base, args.head

    # Gather diff stats
    try:
        files = list_changed_files(base, head)
    except subprocess.CalledProcessError as e:
        print(f"Failed to read git diff: {e}", file=sys.stderr)
        return 2

    try:
        added, deleted, per_file = parse_numstat(base, head)
    except subprocess.CalledProcessError as e:
        print(f"Failed to read numstat: {e}", file=sys.stderr)
        return 2

    files_touched = len(files)
    total_changed = added + deleted
    subtraction_ratio = (deleted / total_changed) if total_changed > 0 else 0.0

    docs_touched = sum(1 for f in files if is_doc(f))
    tests_touched = sum(1 for f in files if is_test(f))
    doc_test_depth = (docs_touched + tests_touched) / files_touched if files_touched else 0.0

    # Optional GitHub API metrics
    token = os.environ.get("GITHUB_TOKEN")
    api_base = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    repo = args.repo
    pr_number = args.pr_number

    cycle_time_hours: Optional[float] = None
    merge_velocity: Optional[int] = None

    if token and repo and pr_number:
        try:
            cycle_time_hours = compute_cycle_time_hours(repo, pr_number, token, api_base)
        except Exception:
            cycle_time_hours = None
        try:
            mv = merged_prs_last_7d(repo, token, api_base)
            merge_velocity = mv if mv is not None else None
        except Exception:
            merge_velocity = None

    # Targets for normalization
    targets = {
        "merge_velocity": 5.0,           # PRs/week (>= better)
        "defect_recovery": 24.0,         # hours (<= better)
        "subtraction_ratio": 0.20,       # fraction (>= better)
        "doc_test_depth": 0.80,          # fraction (>= better)
        "cycle_time": 48.0,              # hours (<= better)
    }

    weights = load_eff_weights()

    # Scores (0..1) with simple normalization
    sr_score = clamp01((subtraction_ratio / targets["subtraction_ratio"]) if targets["subtraction_ratio"] else None)
    dtd_score = clamp01((doc_test_depth / targets["doc_test_depth"]) if targets["doc_test_depth"] else None)
    mv_score = clamp01((merge_velocity / targets["merge_velocity"]) if (merge_velocity is not None and targets["merge_velocity"]) else None)
    ct_score = None
    if cycle_time_hours and cycle_time_hours > 0:
        ct_score = clamp01(targets["cycle_time"] / cycle_time_hours)
    elif cycle_time_hours == 0:
        ct_score = 1.0

    # defect_recovery not computed here; reserved for future signals
    dr_score = None

    # Compute weighted NSS (partial if not all present)
    components: list[Tuple[str, Optional[float], float]] = [
        ("merge_velocity", mv_score, float(weights.get("merge_velocity", 0.30))),
        ("defect_recovery", dr_score, float(weights.get("defect_recovery", 0.25))),
        ("subtraction_ratio", sr_score, float(weights.get("subtraction_ratio", 0.15))),
        ("doc_test_depth", dtd_score, float(weights.get("doc_test_depth", 0.15))),
        ("cycle_time", ct_score, float(weights.get("cycle_time", 0.15))),
    ]

    num = 0.0
    den = 0.0
    for key, s, w in components:
        if s is not None:
            num += s * w
            den += w
    partial_nss = (num / den) if den > 0 else None

    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()
    record = {
        "timestamp": now,
        "pr_number": pr_number or None,
        "files_touched": files_touched,
        "loc_added": added,
        "loc_deleted": deleted,
        "total_changed": total_changed,
        "subtraction_ratio": round(subtraction_ratio, 4),
        "docs_touched": docs_touched,
        "tests_touched": tests_touched,
        "doc_test_depth": round(doc_test_depth, 4),
        "cycle_time_hours": round(cycle_time_hours, 2) if cycle_time_hours is not None else None,
        "merge_velocity": merge_velocity,
        "scores": {
            "merge_velocity": mv_score,
            "defect_recovery": dr_score,
            "subtraction_ratio": sr_score,
            "doc_test_depth": dtd_score,
            "cycle_time": ct_score,
        },
        "partial_nss": round(partial_nss, 4) if partial_nss is not None else None,
        "weights": weights,
        "targets": targets,
    }

    # Ensure output dir exists
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    # Human summary (Markdown-friendly)
    def pct(x: Optional[float]) -> str:
        return f"{x*100:.1f}%" if x is not None else "–"

    summary_lines = [
        "EFF Metrics Summary",
        "",
        f"Files touched: {files_touched} | LOC ±: +{added}/-{deleted} | PR size: {total_changed} LOC",
        f"Subtraction ratio: {record['subtraction_ratio']} (target ≥ {targets['subtraction_ratio']})",
        f"Doc+Test depth: {record['doc_test_depth']} (target ≥ {targets['doc_test_depth']})",
        f"Cycle time: {record['cycle_time_hours']} h (target ≤ {targets['cycle_time']})",
        f"Merge velocity (last 7d): {merge_velocity} (target ≥ {int(targets['merge_velocity'])})",
        f"Partial NSS: {pct(partial_nss)}",
    ]
    summary = "\n".join(summary_lines)

    print(summary)

    if args.post_comment and token and repo and pr_number:
        try:
            post_github_comment(repo, pr_number, summary, token, api_base)
            print("Posted PR comment with EFF metrics.")
        except Exception as e:
            print(f"Failed to post PR comment: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())

