#!/usr/bin/env python3
"""Builds the SVGs and the stats section of the GitHub profile README.

Only aggregate numbers are published: no private repository name ever reaches
the output. Standard library only, so the workflow needs no install step.

    python scripts/build_profile.py --hero-only   # banner only, no token needed
    GH_STATS_TOKEN=... python scripts/build_profile.py
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

LOGIN = "bernardocecchetto"
ROOT = Path(__file__).resolve().parent.parent
START, END = "<!--STATS:START-->", "<!--STATS:END-->"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

THEMES = {
    "light": {
        "ink": "#1f2328", "muted": "#59636e", "line": "#d1d9e0", "surface": "#ffffff",
        "accent": "#0f766e", "levels": ["#ebeff2", "#a7e3d9", "#5cc4b4", "#1f9c8c", "#0f6b61"],
    },
    "dark": {
        "ink": "#f0f6fc", "muted": "#9198a1", "line": "#30363d", "surface": "#0d1117",
        "accent": "#5eead4", "levels": ["#1b2129", "#10504a", "#167a6e", "#2bb09e", "#6fe6d4"],
    },
}

CONTRIB_FIELDS = """
  totalCommitContributions restrictedContributionsCount
  totalPullRequestContributions totalPullRequestReviewContributions
"""
BASE_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    repositoriesContributedTo(first: 100, includeUserRepositories: true,
      contributionTypes: [COMMIT, PULL_REQUEST, PULL_REQUEST_REVIEW]) {
      totalCount
      nodes {
        isFork
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      %s
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
""" % CONTRIB_FIELDS
YEAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) { %s }
  }
}
""" % CONTRIB_FIELDS


def graphql(token, query, **variables):
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"Bearer {token}", "User-Agent": LOGIN},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"]))
    return payload["data"]["user"]


def summarize(collection):
    return {
        "commits": collection["totalCommitContributions"] + collection["restrictedContributionsCount"],
        "prs": collection["totalPullRequestContributions"],
        "reviews": collection["totalPullRequestReviewContributions"],
    }


def fetch(token):
    user = graphql(token, BASE_QUERY, login=LOGIN)
    now = dt.datetime.now(dt.timezone.utc)
    years = {}
    for year in range(int(user["createdAt"][:4]), now.year + 1):
        data = graphql(
            token, YEAR_QUERY, login=LOGIN,
            **{"from": f"{year}-01-01T00:00:00Z",
               "to": min(now, dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")},
        )
        years[str(year)] = summarize(data["contributionsCollection"])

    sizes = Counter()
    for repo in user["repositoriesContributedTo"]["nodes"]:
        if repo["isFork"]:
            continue
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] += edge["size"]

    collection = user["contributionsCollection"]
    return {
        "years": years,
        "last_year": summarize(collection),
        "repos": user["repositoriesContributedTo"]["totalCount"],
        "languages": sizes.most_common(6),
        "days": [d for w in collection["contributionCalendar"]["weeks"] for d in w["contributionDays"]],
    }


def svg(width, height, title, body, extra_css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title, quote=True)}">'
        f"<title>{html.escape(title)}</title>"
        f"<style>text{{font-family:{FONT}}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        f"{extra_css}</style>{body}</svg>\n"
    )


def text(x, y, value, size, fill, weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}">{html.escape(str(value))}</text>')


def hero(theme):
    t = THEMES[theme]
    stages = ["Documents & data", "OCR & retrieval", "Agents & tools", "APIs & infra", "Production"]
    width, y = 840, 142
    xs = [84 + i * 168 for i in range(len(stages))]
    body = text(24, 54, "Bernardo Cecchetto", 34, t["ink"], 700)
    body += text(24, 86, "AI Engineer. I take AI from prototype to production.", 17, t["muted"])
    body += f'<line x1="{xs[0]}" y1="{y}" x2="{xs[-1]}" y2="{y}" stroke="{t["line"]}" stroke-width="2"/>'
    for x, stage in zip(xs, stages):
        last = stage == "Production"
        body += (f'<circle cx="{x}" cy="{y}" r="7" fill="{t["accent"] if last else t["surface"]}" '
                 f'stroke="{t["accent"]}" stroke-width="2"/>')
        body += text(x, y + 30, stage, 13, t["ink"] if last else t["muted"], 600 if last else 400, "middle")
    body += f'<circle class="pulse" cy="{y}" r="4" cx="{xs[0]}" fill="{t["accent"]}"/>'
    css = (f".pulse{{animation:run 5s ease-in-out infinite}}"
           f"@keyframes run{{0%{{transform:translateX(0);opacity:0}}8%{{opacity:1}}"
           f"85%{{transform:translateX({xs[-1] - xs[0]}px);opacity:1}}100%{{transform:translateX({xs[-1] - xs[0]}px);opacity:0}}}}")
    return svg(width, 196, "Bernardo Cecchetto, AI Engineer", body, css)


def streaks(days):
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    longest = run = 0
    for day in days:
        run = run + 1 if day["contributionCount"] else 0
        longest = max(longest, run)
    return longest, sum(1 for d in days if d["contributionCount"] and d["date"] <= today)


def stats_card(theme, data):
    t = THEMES[theme]
    totals = Counter()
    for year in data["years"].values():
        totals.update(year)
    longest, active = streaks(data["days"])
    tiles = [
        ("Commits", totals["commits"], f'{data["last_year"]["commits"]:,} in the last 12 months'),
        ("Pull requests", totals["prs"], f'{data["last_year"]["prs"]:,} in the last 12 months'),
        ("Code reviews", totals["reviews"], f'{data["last_year"]["reviews"]:,} in the last 12 months'),
        ("Active days", active, f"longest streak: {longest} days"),
    ]
    body, css = "", ".tile{opacity:0;animation:in .6s ease-out forwards}@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
    for i, (label, value, sub) in enumerate(tiles):
        x = 24 + i * 200
        body += f'<g class="tile" style="animation-delay:{i * 0.15}s">'
        body += text(x, 34, label, 14, t["muted"])
        body += text(x, 76, f"{value:,}", 36, t["ink"], 700)
        body += text(x, 100, sub, 12, t["muted"])
        body += "</g>"
    return svg(840, 118, "Contribution totals: commits, pull requests, reviews and active days", body, css)


def activity_card(theme, data):
    t = THEMES[theme]
    days = data["days"]
    peak = max((d["contributionCount"] for d in days), default=0) or 1
    cell, gap, left, top = 12, 3, 24, 34
    body = text(24, 20, "Last 12 months", 14, t["ink"], 600)
    first = dt.date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7
    seen_month = None
    weeks = 0
    for i, day in enumerate(days):
        date = dt.date.fromisoformat(day["date"])
        column, row = (i + offset) // 7, (date.weekday() + 1) % 7
        weeks = column
        count = day["contributionCount"]
        level = 0 if not count else min(4, 1 + (count * 4 - 1) // peak)
        x, y = left + column * (cell + gap), top + 18 + row * (cell + gap)
        body += (f'<rect class="c" style="animation-delay:{column * 0.018:.3f}s" x="{x}" y="{y}" '
                 f'width="{cell}" height="{cell}" rx="3" fill="{t["levels"][level]}"/>')
        if row == 0 and date.month != seen_month and date.day <= 7:
            seen_month = date.month
            body += text(x, top + 8, date.strftime("%b"), 11, t["muted"])
    legend_x = left + (weeks + 1) * (cell + gap) - 5 * (cell + gap) - 72
    legend_y = top + 18 + 7 * (cell + gap) + 18
    body += text(legend_x - 6, legend_y, "Less", 11, t["muted"], anchor="end")
    for i, color in enumerate(t["levels"]):
        body += f'<rect x="{legend_x + i * (cell + gap)}" y="{legend_y - 10}" width="{cell}" height="{cell}" rx="3" fill="{color}"/>'
    body += text(legend_x + 5 * (cell + gap) + 2, legend_y, "More", 11, t["muted"])
    css = ".c{opacity:0;animation:f .35s ease-out forwards}@keyframes f{to{opacity:1}}"
    return svg(840, legend_y + 8, "Contribution calendar for the last 12 months", body, css)


def languages_card(theme, data):
    t = THEMES[theme]
    languages = data["languages"]
    total = sum(size for _, size in languages) or 1
    body = text(24, 20, "Languages in the repositories I work on", 14, t["ink"], 600)
    for i, (name, size) in enumerate(languages):
        y = 42 + i * 26
        width = max(4, size / languages[0][1] * 560)
        body += text(24, y + 11, name, 13, t["ink"])
        body += f'<rect class="b" x="150" y="{y}" width="{width:.1f}" height="14" rx="4" fill="{t["levels"][3]}"/>'
        body += text(150 + width + 8, y + 11, f"{size / total:.0%}", 12, t["muted"])
    css = ".b{transform-origin:150px 0;animation:g .9s ease-out both}@keyframes g{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    return svg(840, 42 + len(languages) * 26 + 6, "Languages by code size", body, css)


def picture(name, alt):
    base = f"./assets/{name}"
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{base}-dark.svg">'
            f'<img alt="{alt}" src="{base}-light.svg" width="100%"></picture>')


def section(data):
    rows = "\n".join(
        f'| {year} | {v["commits"]:,} | {v["prs"]:,} | {v["reviews"]:,} |'
        for year, v in sorted(data["years"].items(), reverse=True)
        if any(v.values())
    )
    updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    return f"""## Activity

{picture("stats", "Commits, pull requests, code reviews and active days")}

{picture("activity", "Contribution calendar for the last 12 months")}

<details>
<summary><b>Year by year and languages</b></summary>
<br>

| Year | Commits | Pull requests | Reviews |
|:---|---:|---:|---:|
{rows}

{picture("languages", "Languages by code size")}

</details>

<sub>Includes private work, in aggregate. Refreshed daily by a GitHub Action, last on {updated}.</sub>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hero-only", action="store_true")
    parser.add_argument("--fixture", help="JSON file used instead of the GitHub API")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root)
    (root / "assets").mkdir(parents=True, exist_ok=True)

    for theme in THEMES:
        (root / "assets" / f"hero-{theme}.svg").write_text(hero(theme))
    if args.hero_only:
        return

    if args.fixture:
        data = json.loads(Path(args.fixture).read_text())
    else:
        token = os.environ.get("GH_STATS_TOKEN")
        if not token:
            sys.exit("GH_STATS_TOKEN is not set: stats left out rather than published with public data only.")
        data = fetch(token)

    # Never publish an empty card: a token without access would otherwise show zeros.
    if not any(d["contributionCount"] for d in data["days"]):
        sys.exit("No contributions visible to this token: README left unchanged.")

    for theme in THEMES:
        (root / "assets" / f"stats-{theme}.svg").write_text(stats_card(theme, data))
        (root / "assets" / f"activity-{theme}.svg").write_text(activity_card(theme, data))
        (root / "assets" / f"languages-{theme}.svg").write_text(languages_card(theme, data))

    readme = root / "README.md"
    content = readme.read_text()
    if START not in content or END not in content:
        sys.exit("Stats markers are missing from README.md.")
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    readme.write_text(pattern.sub(lambda _: f"{START}\n{section(data)}\n{END}", content))


if __name__ == "__main__":
    main()
