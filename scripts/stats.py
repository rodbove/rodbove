import json
import math
import os
import sys
import urllib.request
from datetime import date, timedelta

USER = "rodbove"
QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""

W, H = 800, 330
BODY, SIDE, EDGE = "#9d9e99", "#6c6d69", "#7a7b76"
INK, DIM_INK = "#1c1c1c", "#454642"
SCREEN, S_INK, S_DIM, S_FAINT = "#0d0e0f", "#eceae4", "#6a6b6c", "#222325"
ORANGE, BLUE, GREEN, WHITE = "#ff5b14", "#2f6bd8", "#2fa35a", "#f4f3ef"
PAD, PAD_OFF, PAD_SH, KEY, GRILLE = "#dddd d7".replace(" ", ""), "#c4c4be", "#5e5f5b", "#2a2a2a", "#555652"
LEVELS = ["#ffd2bd", "#ffa070", "#ff7a3d", ORANGE]
KNOB_COLORS = [BLUE, GREEN, WHITE, ORANGE]
SWEEP = 8.0
SHORT = {"typescript": "ts", "javascript": "js", "kotlin": "kt", "vim script": "vim", "shell": "sh", "python": "py", "dockerfile": "dock"}


def fetch():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def streaks(days):
    counts = [(date.fromisoformat(d["date"]), d["contributionCount"]) for d in days]
    best = run = 0
    for _, n in counts:
        run = run + 1 if n > 0 else 0
        best = max(best, run)
    current = 0
    items = list(reversed(counts))
    if items and items[0][1] == 0:
        items = items[1:]
    for _, n in items:
        if n == 0:
            break
        current += 1
    return current, best


def languages(repos, count=6):
    sizes = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes[name] = sizes.get(name, 0) + edge["size"]
    total = sum(sizes.values()) or 1
    top = sorted(sizes.items(), key=lambda kv: -kv[1])[:count]
    return [(name, size / total) for name, size in top]


def level(n, peak):
    if n == 0:
        return None
    return LEVELS[min(len(LEVELS) - 1, int(math.ceil(n / max(peak, 1) * len(LEVELS))) - 1)]


def render(data):
    user = data["data"]["user"]
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    weeks = cal["weeks"][-52:]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    current, best = streaks(days)
    langs = languages(user["repositories"]["nodes"])
    stars = sum(r["stargazerCount"] for r in user["repositories"]["nodes"])
    peak = sorted(d["contributionCount"] for w in weeks for d in w["contributionDays"])
    peak = peak[int(len(peak) * 0.95)] if peak else 1
    out = []
    a = out.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    a("<style>")
    a('text { font-family: "SF Mono", "Cascadia Code", Menlo, Consolas, "DejaVu Sans Mono", monospace; }')
    a(f".i {{ fill: {S_INK}; }} .d {{ fill: {S_DIM}; }} .o {{ fill: {ORANGE}; }} .b {{ font-weight: 700; }}")
    a(f".lbl {{ fill: {DIM_INK}; font-size: 9px; letter-spacing: 1px; }}")
    a("@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }")
    a(".blink { animation: blink 1s step-end infinite; }")
    a(f"@keyframes sweep {{ 0% {{ transform: translateX(0px); }} 100% {{ transform: translateX({52 * 13}px); }} }}")
    a(f".sweep {{ animation: sweep {SWEEP}s linear infinite; }}")
    a("</style>")
    a("<defs>")
    a(f'<linearGradient id="body" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a9aaa5"/><stop offset="1" stop-color="{BODY}"/></linearGradient>')
    a('<radialGradient id="knob" cx="0.4" cy="0.35" r="0.7"><stop offset="0" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="1" stop-color="#000000" stop-opacity="0.15"/></radialGradient>')
    a('<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0.07"/><stop offset="0.5" stop-color="#ffffff" stop-opacity="0"/></linearGradient>')
    a('<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff" stop-opacity="0"/><stop offset="1" stop-color="#ffffff" stop-opacity="0.45"/></linearGradient>')
    a('<clipPath id="grid"><rect x="58" y="196" width="680" height="94"/></clipPath>')
    a("</defs>")

    a(f'<rect x="4" y="10" width="{W - 8}" height="{H - 12}" rx="22" fill="{SIDE}"/>')
    a(f'<rect x="4" y="4" width="{W - 8}" height="{H - 14}" rx="22" fill="url(#body)" stroke="{EDGE}" stroke-width="1.5"/>')
    for x, y in [(22, 22), (W - 22, 22), (22, H - 28), (W - 22, H - 28)]:
        a(f'<circle cx="{x}" cy="{y}" r="4" fill="{EDGE}"/><path d="M{x - 2.5} {y} h5" stroke="{DIM_INK}" stroke-width="1"/>')

    sx, sy, sw, sh = 40, 34, 250, 118
    a(f'<rect x="{sx - 8}" y="{sy - 8}" width="{sw + 16}" height="{sh + 16}" rx="10" fill="{KEY}"/>')
    a(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="5" fill="{SCREEN}"/>')
    a(f'<text x="{sx + 12}" y="{sy + 18}" font-size="10" class="o b">CONTRIB</text>')
    a(f'<text x="{sx + sw - 12}" y="{sy + 18}" font-size="10" text-anchor="end" class="d">LAST 12 MONTHS</text>')
    a(f'<text x="{sx + 12}" y="{sy + 58}" font-size="38" class="i b">{cal["totalContributions"]}</text>')
    a(f'<path d="M{sx + 10} {sy + 72} H{sx + sw - 10}" stroke="{S_FAINT}"/>')
    cells = [("STREAK", f"{current}d"), ("BEST", f"{best}d"), ("STARS", str(stars))]
    for k, (key, val) in enumerate(cells):
        x = sx + 12 + k * 80
        a(f'<text x="{x}" y="{sy + 90}" font-size="9" class="d">{key}</text>')
        a(f'<text x="{x}" y="{sy + 108}" font-size="15" class="i b">{val}</text>')
    a(f'<text x="{sx + sw - 12}" y="{sy + 108}" font-size="15" class="o blink">_</text>')
    a(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="5" fill="url(#glass)"/>')

    knobs = [
        ("COMMITS", cc["totalCommitContributions"], 400),
        ("PRS", cc["totalPullRequestContributions"], 50),
        ("ISSUES", cc["totalIssueContributions"], 50),
        ("REPOS", user["repositories"]["totalCount"], 60),
    ]
    for k, (name, value, full) in enumerate(knobs):
        cx, cy = 345 + k * 62, 72
        c = KNOB_COLORS[k]
        ang = -135 + 270 * min(1.0, value / full)
        for t in range(11):
            ta = math.radians(-225 + 27 * t)
            a(f'<path d="M{cx + 24 * math.cos(ta):.1f} {cy + 24 * math.sin(ta):.1f} L{cx + 27 * math.cos(ta):.1f} {cy + 27 * math.sin(ta):.1f}" stroke="{DIM_INK}" stroke-width="1"/>')
        a(f'<circle cx="{cx}" cy="{cy + 2}" r="19" fill="{PAD_SH}"/>')
        a(f'<circle cx="{cx}" cy="{cy}" r="19" fill="{c}"/>')
        a(f'<circle cx="{cx}" cy="{cy}" r="19" fill="url(#knob)"/>')
        a(f'<g transform="rotate({ang:.1f} {cx} {cy})"><rect x="{cx - 1.5}" y="{cy - 17}" width="3" height="9" rx="1.5" fill="{INK if c == WHITE else WHITE}"/></g>')
        a(f'<text x="{cx}" y="{cy + 42}" text-anchor="middle" class="lbl">{name}</text>')
        a(f'<text x="{cx}" y="{cy + 56}" text-anchor="middle" font-size="11" fill="{INK}" class="b">{value}</text>')

    fx0, fy, fh = 600, 36, 100
    for k, (name, share) in enumerate(langs):
        x = fx0 + k * 30
        a(f'<rect x="{x - 2}" y="{fy}" width="4" height="{fh}" rx="2" fill="{KEY}"/>')
        for t in range(6):
            a(f'<path d="M{x - 9} {fy + t * fh / 5:.1f} h4" stroke="{DIM_INK}" stroke-width="0.8"/>')
        cap = fy + fh - fh * min(1.0, share / max(langs[0][1], 0.01))
        a(f'<rect x="{x - 9}" y="{cap - 6 + 2:.1f}" width="18" height="12" rx="2" fill="{PAD_SH}"/>')
        a(f'<rect x="{x - 9}" y="{cap - 6:.1f}" width="18" height="12" rx="2" fill="{KNOB_COLORS[k % 4]}"/>')
        a(f'<path d="M{x - 7} {cap:.1f} h14" stroke="{INK if k % 4 == 2 else WHITE}" stroke-width="1.2"/>')
        label = SHORT.get(name.lower(), name.lower()[:4])
        a(f'<text x="{x}" y="{fy + fh + 18}" text-anchor="middle" font-size="8" fill="{DIM_INK}">{label}</text>')
        a(f'<text x="{x}" y="{fy + fh + 30}" text-anchor="middle" font-size="9" fill="{INK}" class="b">{share * 100:.0f}%</text>')

    gx, gy, cell, gap = 62, 200, 11, 2
    last_month = None
    for wi, week in enumerate(weeks):
        x = gx + wi * (cell + gap)
        first = week["contributionDays"][0]["date"]
        month = first[5:7]
        if month != last_month and wi < 51:
            name = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"][int(month) - 1]
            a(f'<text x="{x}" y="{gy - 6}" class="lbl" font-size="8">{name}</text>')
            last_month = month
        for d in week["contributionDays"]:
            wd = (date.fromisoformat(d["date"]).weekday() + 1) % 7
            y = gy + wd * (cell + gap)
            fill = level(d["contributionCount"], peak) or PAD_OFF
            a(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{fill}"><title>{d["date"]}: {d["contributionCount"]}</title></rect>')
    for wd, name in [(1, "MON"), (3, "WED"), (5, "FRI")]:
        a(f'<text x="{gx - 6}" y="{gy + wd * (cell + gap) + 9}" text-anchor="end" class="lbl" font-size="7">{name}</text>')
    a(f'<g clip-path="url(#grid)"><g class="sweep"><rect x="{gx - 30}" y="{gy - 2}" width="30" height="{7 * (cell + gap) + 2}" fill="url(#beam)"/></g></g>')
    lx = gx + 52 * (cell + gap) - 120
    a(f'<text x="{lx - 6}" y="{gy + 7 * (cell + gap) + 16}" text-anchor="end" class="lbl" font-size="8">LESS</text>')
    for k, c in enumerate([PAD_OFF] + LEVELS):
        a(f'<rect x="{lx + k * 14}" y="{gy + 7 * (cell + gap) + 8}" width="{cell}" height="{cell}" rx="2.5" fill="{c}"/>')
    a(f'<text x="{lx + 5 * 14 + 4}" y="{gy + 7 * (cell + gap) + 16}" class="lbl" font-size="8">MORE</text>')
    a(f'<text x="{gx}" y="{gy + 7 * (cell + gap) + 16}" class="lbl" font-size="8">UPDATED {date.today().isoformat()}</text>')
    a("</svg>")
    return "\n".join(out)


def main():
    data = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else fetch()
    if "errors" in data:
        sys.exit(json.dumps(data["errors"]))
    with open(sys.argv[1], "w") as f:
        f.write(render(data))


if __name__ == "__main__":
    main()
