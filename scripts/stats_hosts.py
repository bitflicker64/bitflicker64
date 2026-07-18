#!/usr/bin/env python3
"""Probe public GitHub-stats card mirrors; pick the first healthy host per slot.

Used by generate_readme.py and .github/workflows/check-stats-hosts.yml.
When the popular free Vercel/Heroku demos go 503/timeout, we fall through
to known working mirrors so the profile README keeps rendering.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

USERNAME = "bitflicker64"
REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_PATH = REPO_ROOT / "stats_hosts.status.json"

# Query strings shared across anuraghazra-compatible mirrors.
_STATS_QS = (
    f"username={USERNAME}&show_icons=true&theme=transparent&hide_border=true"
    f"&title_color=38C2FF&text_color=BDC3CF&icon_color=38C2FF"
    f"&count_private=true&include_all_commits=true"
)
_LANGS_QS = (
    f"username={USERNAME}&layout=compact&theme=transparent&hide_border=true"
    f"&title_color=38C2FF&text_color=BDC3CF&card_width=445"
)
_STREAK_QS = (
    f"user={USERNAME}&theme=transparent&hide_border=true"
    f"&ring=38C2FF&fire=38C2FF&currStreakNum=BDC3CF"
    f"&sideNums=BDC3CF&sideLabels=BDC3CF&currStreakLabel=38C2FF"
)

# Ordered preference: try official/public first, then community mirrors, then
# alternate card providers that still return an SVG.
CANDIDATES: dict[str, list[str]] = {
    "stats": [
        f"https://github-readme-stats.vercel.app/api?{_STATS_QS}",
        f"https://github-readme-stats-one-bice.vercel.app/api?{_STATS_QS}",
        (
            "https://github-profile-summary-cards.vercel.app/api/cards/stats"
            f"?username={USERNAME}&theme=github_dark"
        ),
    ],
    "streak": [
        f"https://streak-stats.demolab.com/?{_STREAK_QS}",
        f"https://github-readme-streak-stats.herokuapp.com/?{_STREAK_QS}",
        (
            "https://github-profile-summary-cards.vercel.app/api/cards/stats"
            f"?username={USERNAME}&theme=github_dark"
        ),
        (
            "https://github-profile-summary-cards.vercel.app/api/cards/profile-details"
            f"?username={USERNAME}&theme=github_dark"
        ),
    ],
    "langs": [
        f"https://github-readme-stats.vercel.app/api/top-langs/?{_LANGS_QS}",
        f"https://github-readme-stats-one-bice.vercel.app/api/top-langs/?{_LANGS_QS}",
        (
            "https://github-profile-summary-cards.vercel.app/api/cards/repos-per-language"
            f"?username={USERNAME}&theme=github_dark"
        ),
        (
            "https://github-profile-summary-cards.vercel.app/api/cards/most-commit-language"
            f"?username={USERNAME}&theme=github_dark"
        ),
    ],
    "activity_graph": [
        (
            "https://github-readme-activity-graph.vercel.app/graph"
            f"?username={USERNAME}&theme=github-compact&hide_border=true&area=true"
        ),
    ],
}

PROBE_TIMEOUT_S = float(os.environ.get("STATS_PROBE_TIMEOUT", "12"))
MIN_SVG_BYTES = 400


@dataclass
class ProbeResult:
    slot: str
    url: str
    ok: bool
    status: int | None
    content_type: str
    bytes: int
    error: str = ""


@dataclass
class Selection:
    slot: str
    url: str
    host: str
    tried: list[dict]
    healthy: bool


def _host(url: str) -> str:
    return urlparse(url).netloc or url


def probe_url(url: str) -> ProbeResult:
    """GET a candidate; healthy if HTTP 200 + looks like an SVG image."""
    headers = {
        "User-Agent": f"{USERNAME}-stats-host-probe",
        "Accept": "image/svg+xml,image/*,*/*",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=PROBE_TIMEOUT_S) as resp:
            status = getattr(resp, "status", 200)
            ctype = (resp.headers.get("Content-Type") or "").lower()
            body = resp.read(64_000)
    except urllib.error.HTTPError as e:
        detail = e.read(200).decode("utf-8", errors="replace")
        return ProbeResult(
            slot="",
            url=url,
            ok=False,
            status=e.code,
            content_type=(e.headers.get("Content-Type") if e.headers else "") or "",
            bytes=0,
            error=detail[:120].replace("\n", " "),
        )
    except Exception as e:  # timeout, DNS, SSL, …
        return ProbeResult(
            slot="",
            url=url,
            ok=False,
            status=None,
            content_type="",
            bytes=0,
            error=f"{type(e).__name__}: {e}",
        )

    head = body.lstrip()[:200].lower()
    looks_svg = (
        b"<svg" in head
        or "image/svg" in ctype
        or head.startswith(b"<?xml")
    )
    # Reject Vercel pause / payment / HTML error pages that snuck through as 200
    bad_markers = (
        b"deployment_paused",
        b"deployment_disabled",
        b"payment required",
        b"<!doctype html",
        b"<html",
    )
    if any(m in head for m in bad_markers):
        looks_svg = False

    ok = status == 200 and looks_svg and len(body) >= MIN_SVG_BYTES
    return ProbeResult(
        slot="",
        url=url,
        ok=ok,
        status=status,
        content_type=ctype,
        bytes=len(body),
        error="" if ok else "not a usable SVG",
    )


def select_slot(slot: str, candidates: Iterable[str]) -> Selection:
    tried: list[dict] = []
    for url in candidates:
        result = probe_url(url)
        result.slot = slot
        tried.append(
            {
                "url": url,
                "host": _host(url),
                "ok": result.ok,
                "status": result.status,
                "bytes": result.bytes,
                "error": result.error,
            }
        )
        label = "OK" if result.ok else "DEAD"
        print(
            f"  [{slot}] {label} {_host(url)} "
            f"(status={result.status} bytes={result.bytes} {result.error[:60]})",
            file=sys.stderr,
        )
        if result.ok:
            return Selection(
                slot=slot,
                url=url,
                host=_host(url),
                tried=tried,
                healthy=True,
            )

    # Nothing worked — keep first candidate as last-resort URL so README still
    # has a link, but mark unhealthy so the workflow can surface it.
    fallback = next(iter(candidates), "")
    print(f"  [{slot}] ALL DEAD — falling back to {fallback[:80]}", file=sys.stderr)
    return Selection(
        slot=slot,
        url=fallback,
        host=_host(fallback) if fallback else "",
        tried=tried,
        healthy=False,
    )


def select_all(candidates: dict[str, list[str]] | None = None) -> dict[str, Selection]:
    pool = candidates or CANDIDATES
    print("Probing stats card mirrors…", file=sys.stderr)
    out: dict[str, Selection] = {}
    for slot, urls in pool.items():
        out[slot] = select_slot(slot, urls)
    return out


def write_status(selections: dict[str, Selection], path: Path = STATUS_PATH) -> dict:
    payload = {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "username": USERNAME,
        "slots": {
            name: {
                "url": sel.url,
                "host": sel.host,
                "healthy": sel.healthy,
                "tried": sel.tried,
            }
            for name, sel in selections.items()
        },
        "all_healthy": all(s.healthy for s in selections.values()),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path}", file=sys.stderr)
    return payload


def urls_for_template(selections: dict[str, Selection]) -> dict[str, str]:
    """Placeholder map consumed by generate_readme.py."""
    return {
        "STATS_CARD_URL": selections["stats"].url,
        "STREAK_CARD_URL": selections["streak"].url,
        "TOP_LANGS_URL": selections["langs"].url,
        "ACTIVITY_GRAPH_URL": selections["activity_graph"].url,
        "STATS_HOSTS_NOTE": _hosts_note(selections),
    }


def _hosts_note(selections: dict[str, Selection]) -> str:
    parts = []
    for name in ("stats", "streak", "langs", "activity_graph"):
        sel = selections[name]
        mark = "✓" if sel.healthy else "✗"
        parts.append(f"{name}={sel.host}{mark}")
    return " · ".join(parts)


def main() -> int:
    selections = select_all()
    payload = write_status(selections)
    # Machine-readable one-liner for Actions step summary
    for name, sel in selections.items():
        state = "healthy" if sel.healthy else "UNHEALTHY"
        print(f"{name}: {state} -> {sel.host}")

    if not payload["all_healthy"]:
        # Non-zero so a dedicated check workflow can notify, but generate_readme
        # still produces a README with best-effort URLs.
        print("WARNING: one or more stats slots have no healthy host", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
