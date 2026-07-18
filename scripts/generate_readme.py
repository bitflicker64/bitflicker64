#!/usr/bin/env python3
"""Fully regenerate profile README.md from README.template.md + GitHub API.

Designed for GitHub Actions (GITHUB_TOKEN) and local runs (gh auth / env token).
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

USERNAME = "bitflicker64"
REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO_ROOT / "README.template.md"
OUTPUT_PATH = REPO_ROOT / "README.md"

# Upstream projects to highlight (order = display priority).
FEATURED_GROUPS: list[dict[str, Any]] = [
    {
        "title": "Apache HugeGraph ecosystem",
        "repos": [
            "apache/hugegraph",
            "apache/hugegraph-ai",
            "apache/hugegraph-doc",
            "apache/hugegraph-toolchain",
        ],
        "logo": "apache",
        "search": "https://github.com/pulls?q=is%3Apr+author%3Abitflicker64+org%3Aapache+hugegraph",
        "blurb": "Docker healthchecks, process supervision, bridge networking, CI, auth, and ops docs.",
    },
    {
        "title": "Cilium / Hubble",
        "repos": ["cilium/cilium"],
        "logo": "cilium",
        "search": "https://github.com/cilium/cilium/pulls?q=is%3Apr+author%3Abitflicker64",
        "blurb": "Hubble metrics label parsing, docs fixes, contributor tooling cleanup.",
    },
    {
        "title": "containerd",
        "repos": ["containerd/containerd"],
        "logo": "containerd",
        "search": "https://github.com/containerd/containerd/pulls?q=is%3Apr+author%3Abitflicker64",
        "blurb": "Content-store size filtering (`AdaptInfo`) and CRI-adjacent work.",
    },
    {
        "title": "Kubernetes ecosystem",
        "repos": [
            "kubernetes/kubernetes",
            "chaos-mesh/chaos-mesh",
            "sustainable-computing-io/kepler",
            "pipe-cd/pipecd",
        ],
        "logo": "kubernetes",
        "search": "https://github.com/pulls?q=is%3Apr+author%3Abitflicker64+(repo%3Akubernetes%2Fkubernetes+OR+repo%3Achaos-mesh%2Fchaos-mesh+OR+repo%3Asustainable-computing-io%2Fkepler+OR+repo%3Apipe-cd%2Fpipecd)",
        "blurb": "Cluster tooling, chaos e2e hygiene, energy exporter manifests, CD docs.",
    },
]

# Open PRs in these repos get radar priority; others still shown.
RADAR_PRIORITY = [
    "apache/hugegraph",
    "apache/hugegraph-ai",
    "apache/hugegraph-doc",
    "cilium/cilium",
    "containerd/containerd",
    "kubernetes/kubernetes",
    "chaos-mesh/chaos-mesh",
    "sustainable-computing-io/kepler",
    "pipe-cd/pipecd",
    "deepchem/deepchem",
    "warpdotdev/warp",
    "NousResearch/hermes-agent",
    "sugarlabs/musicblocks-v4",
    "SakanaAI/LanguageEvolution",
]

ACTIVITY_LIMIT = 10
OPEN_PR_LIMIT = 12
MAX_MERGED_PAGES = 5  # 100 nodes each


def token() -> str | None:
    for key in ("GITHUB_TOKEN", "GH_TOKEN", "GH_PAT"):
        val = os.environ.get(key)
        if val:
            return val
    return None


def api_request(
    url: str,
    *,
    method: str = "GET",
    body: dict | None = None,
    accept: str = "application/vnd.github+json",
) -> Any:
    headers = {
        "Accept": accept,
        "User-Agent": f"{USERNAME}-readme-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    tok = token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {e.code} for {url}: {detail[:500]}") from e


def graphql(query: str, variables: dict | None = None) -> dict:
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables
    result = api_request("https://api.github.com/graphql", method="POST", body=payload)
    if not result:
        raise RuntimeError("Empty GraphQL response")
    if result.get("errors"):
        raise RuntimeError(f"GraphQL errors: {result['errors']}")
    return result["data"]


def fetch_user() -> dict:
    return api_request(f"https://api.github.com/users/{USERNAME}")


def fetch_year_contributions() -> int:
    data = graphql(
        """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar { totalContributions }
            }
          }
        }
        """,
        {"login": USERNAME},
    )
    return int(
        data["user"]["contributionsCollection"]["contributionCalendar"][
            "totalContributions"
        ]
    )


def fetch_all_merged_prs() -> list[dict]:
    """Return merged PR nodes with repository nameWithOwner (paginated)."""
    query = """
    query($login: String!, $cursor: String) {
      user(login: $login) {
        pullRequests(first: 100, states: MERGED, orderBy: {field: UPDATED_AT, direction: DESC}, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            title
            number
            url
            mergedAt
            repository {
              nameWithOwner
              isPrivate
              owner { login }
            }
          }
        }
      }
    }
    """
    nodes: list[dict] = []
    cursor = None
    for _ in range(MAX_MERGED_PAGES):
        data = graphql(query, {"login": USERNAME, "cursor": cursor})
        conn = data["user"]["pullRequests"]
        nodes.extend(conn["nodes"] or [])
        if not conn["pageInfo"]["hasNextPage"]:
            break
        cursor = conn["pageInfo"]["endCursor"]
    return nodes


def fetch_open_prs() -> list[dict]:
    query = """
    query($login: String!) {
      user(login: $login) {
        pullRequests(first: 50, states: OPEN, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            title
            number
            url
            isDraft
            repository {
              nameWithOwner
              owner { login }
            }
          }
        }
      }
    }
    """
    data = graphql(query, {"login": USERNAME})
    return data["user"]["pullRequests"]["nodes"] or []


def fetch_recent_events() -> list[dict]:
    # Public events only (fine for profile). Paginate lightly.
    events = api_request(
        f"https://api.github.com/users/{USERNAME}/events/public?per_page=30"
    )
    return events or []


def is_upstream(repo_owner: str) -> bool:
    return repo_owner.lower() != USERNAME.lower()


def format_activity(events: list[dict]) -> str:
    lines: list[str] = []
    for ev in events:
        if len(lines) >= ACTIVITY_LIMIT:
            break
        et = ev.get("type")
        repo = (ev.get("repo") or {}).get("name", "")
        repo_url = f"https://github.com/{repo}"
        payload = ev.get("payload") or {}

        if et == "PushEvent":
            size = payload.get("size") or len(payload.get("commits") or [])
            ref = (payload.get("ref") or "").replace("refs/heads/", "")
            lines.append(
                f"1. ⬆️ Pushed {size} commit(s) to `{ref}` in [{repo}]({repo_url})"
            )
        elif et == "PullRequestEvent":
            pr = payload.get("pull_request") or {}
            action = payload.get("action", "updated")
            num = pr.get("number") or payload.get("number")
            title = pr.get("title") or "pull request"
            url = pr.get("html_url") or f"{repo_url}/pull/{num}"
            emoji = {
                "opened": "📤",
                "closed": "❌",
                "reopened": "♻️",
                "synchronize": "🔄",
            }.get(action, "🔀")
            if action == "closed" and pr.get("merged"):
                emoji, action = "✅", "merged"
            lines.append(
                f"1. {emoji} {action.capitalize()} PR [#{num}]({url}) — {title} in [{repo}]({repo_url})"
            )
        elif et == "IssuesEvent":
            issue = payload.get("issue") or {}
            action = payload.get("action", "updated")
            num = issue.get("number")
            title = issue.get("title") or "issue"
            url = issue.get("html_url") or f"{repo_url}/issues/{num}"
            emoji = "🐛" if action == "opened" else "ℹ️"
            lines.append(
                f"1. {emoji} {action.capitalize()} issue [#{num}]({url}) — {title} in [{repo}]({repo_url})"
            )
        elif et == "IssueCommentEvent":
            comment = payload.get("comment") or {}
            issue = payload.get("issue") or {}
            num = issue.get("number")
            url = comment.get("html_url") or issue.get("html_url") or repo_url
            kind = "PR" if issue.get("pull_request") else "issue"
            lines.append(
                f"1. 🗣 Commented on {kind} [#{num}]({url}) in [{repo}]({repo_url})"
            )
        elif et == "PullRequestReviewEvent":
            pr = payload.get("pull_request") or {}
            num = pr.get("number")
            url = pr.get("html_url") or repo_url
            lines.append(
                f"1. 👀 Reviewed PR [#{num}]({url}) in [{repo}]({repo_url})"
            )
        elif et == "CreateEvent":
            ref_type = payload.get("ref_type", "ref")
            ref = payload.get("ref") or ""
            lines.append(
                f"1. 🌱 Created {ref_type} `{ref}` in [{repo}]({repo_url})"
            )
        elif et == "WatchEvent":
            lines.append(f"1. ⭐ Starred [{repo}]({repo_url})")
        elif et == "ForkEvent":
            lines.append(f"1. 🍴 Forked [{repo}]({repo_url})")
        elif et == "ReleaseEvent":
            rel = payload.get("release") or {}
            tag = rel.get("tag_name") or "release"
            url = rel.get("html_url") or repo_url
            lines.append(f"1. 🚀 Released [{tag}]({url}) in [{repo}]({repo_url})")
        else:
            continue

    if not lines:
        return "_No recent public activity found._"
    return "\n".join(lines)


def format_open_prs(prs: list[dict]) -> str:
    upstream = [
        p
        for p in prs
        if p.get("repository")
        and is_upstream(p["repository"]["owner"]["login"])
        and not p.get("isDraft")
    ]

    def sort_key(p: dict) -> tuple:
        full = p["repository"]["nameWithOwner"]
        try:
            pri = RADAR_PRIORITY.index(full)
        except ValueError:
            pri = 999
        return (pri, full, -int(p.get("number") or 0))

    upstream.sort(key=sort_key)
    chosen = upstream[:OPEN_PR_LIMIT]
    if not chosen:
        return "_No open upstream PRs right now — check back after the next contribution wave._"

    lines = []
    for p in chosen:
        full = p["repository"]["nameWithOwner"]
        title = re.sub(r"\s+", " ", (p.get("title") or "").strip())
        if len(title) > 90:
            title = title[:87] + "…"
        lines.append(
            f"- [{full}#{p['number']}]({p['url']}) — {title}"
        )
    return "\n".join(lines)


def format_featured(merged: list[dict], open_prs: list[dict]) -> str:
    merged_by_repo: dict[str, list[dict]] = defaultdict(list)
    open_by_repo: dict[str, list[dict]] = defaultdict(list)

    for pr in merged:
        repo = pr.get("repository") or {}
        owner = (repo.get("owner") or {}).get("login", "")
        if not is_upstream(owner):
            continue
        full = repo.get("nameWithOwner")
        if full:
            merged_by_repo[full].append(pr)

    for pr in open_prs:
        repo = pr.get("repository") or {}
        owner = (repo.get("owner") or {}).get("login", "")
        if not is_upstream(owner) or pr.get("isDraft"):
            continue
        full = repo.get("nameWithOwner")
        if full:
            open_by_repo[full].append(pr)

    cards: list[str] = []
    for group in FEATURED_GROUPS:
        m_count = sum(len(merged_by_repo.get(r, [])) for r in group["repos"])
        o_count = sum(len(open_by_repo.get(r, [])) for r in group["repos"])

        # Highlight a sample merged PR (most recently merged in group).
        samples: list[dict] = []
        for r in group["repos"]:
            samples.extend(merged_by_repo.get(r, []))
        samples.sort(key=lambda p: p.get("mergedAt") or "", reverse=True)
        sample_html = ""
        if samples:
            s = samples[0]
            st = re.sub(r"\s+", " ", (s.get("title") or "").strip())
            if len(st) > 70:
                st = st[:67] + "…"
            sample_html = (
                f'<br><sub>Latest: <a href="{s["url"]}">#{s["number"]}</a> — {st}</sub>'
            )
        elif o_count:
            # Fall back to an open PR highlight.
            opens: list[dict] = []
            for r in group["repos"]:
                opens.extend(open_by_repo.get(r, []))
            if opens:
                s = opens[0]
                st = re.sub(r"\s+", " ", (s.get("title") or "").strip())
                if len(st) > 70:
                    st = st[:67] + "…"
                sample_html = (
                    f'<br><sub>Open: <a href="{s["url"]}">#{s["number"]}</a> — {st}</sub>'
                )

        badge = f'{m_count} merged'
        if o_count:
            badge += f' · {o_count} open'

        cards.append(
            f"""    <td width="50%" valign="top">
      <h3 align="center">{group["title"]}</h3>
      <div align="center">
        <a href="{group["search"]}">
          <img src="https://img.shields.io/badge/{urllib.parse.quote(badge)}-38C2FF?style=flat-square&logo={group["logo"]}"/>
        </a>
        <br>
        <span>{group["blurb"]}</span>
        {sample_html}
      </div>
    </td>"""
        )

    # 2x2 table
    rows = []
    for i in range(0, len(cards), 2):
        left = cards[i]
        right = cards[i + 1] if i + 1 < len(cards) else "    <td width=\"50%\"></td>"
        rows.append(f"  <tr>\n{left}\n{right}\n  </tr>")

    return "<table>\n" + "\n".join(rows) + "\n</table>"


def count_upstream_merged(merged: list[dict]) -> int:
    n = 0
    for pr in merged:
        repo = pr.get("repository") or {}
        owner = (repo.get("owner") or {}).get("login", "")
        if is_upstream(owner):
            n += 1
    return n


def select_stats_hosts() -> dict[str, str]:
    """Probe mirrors and return template placeholders for stats image URLs."""
    # Local import keeps this script runnable even if stats_hosts is edited alone.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from stats_hosts import select_all, urls_for_template, write_status  # type: ignore

    selections = select_all()
    write_status(selections)
    return urls_for_template(selections)


def render() -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    # Strip the source-of-truth comment block from generated README (optional keep first line note).
    template = re.sub(
        r"^<!--.*?-->\n",
        "<!-- AUTO-GENERATED from README.template.md — do not edit by hand -->\n",
        template,
        count=1,
        flags=re.DOTALL,
    )

    print("Selecting healthy stats hosts…", file=sys.stderr)
    stats_urls = select_stats_hosts()

    print("Fetching user…", file=sys.stderr)
    user = fetch_user()
    print("Fetching contributions…", file=sys.stderr)
    year_contribs = fetch_year_contributions()
    print("Fetching merged PRs…", file=sys.stderr)
    merged = fetch_all_merged_prs()
    print("Fetching open PRs…", file=sys.stderr)
    open_prs = fetch_open_prs()
    print("Fetching recent events…", file=sys.stderr)
    events = fetch_recent_events()

    upstream = count_upstream_merged(merged)
    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    replacements = {
        "UPSTREAM_MERGED": str(upstream),
        "YEAR_CONTRIBUTIONS": str(year_contribs),
        "PUBLIC_REPOS": str(user.get("public_repos", "")),
        "FOLLOWERS": str(user.get("followers", "")),
        "FEATURED_WORK": format_featured(merged, open_prs),
        "OPEN_PRS": format_open_prs(open_prs),
        "RECENT_ACTIVITY": format_activity(events),
        "LAST_UPDATED": last_updated,
        **stats_urls,
    }

    out = template
    for key, val in replacements.items():
        out = out.replace("{{" + key + "}}", val)

    leftover = re.findall(r"\{\{[A-Z0-9_]+\}\}", out)
    if leftover:
        raise RuntimeError(f"Unreplaced placeholders: {leftover}")

    return out


def main() -> int:
    try:
        content = render()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
