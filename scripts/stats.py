import json
import math
import os
import sys
import urllib.request
from datetime import date

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

W, H = 800, 250
BODY, SIDE, EDGE = "#9d9e99", "#6c6d69", "#7a7b76"
INK, DIM_INK = "#1c1c1c", "#454642"
SCREEN, S_INK, S_DIM, S_FAINT = "#0d0e0f", "#eceae4", "#6a6b6c", "#222325"
ORANGE, BLUE, GREEN, WHITE = "#ff5b14", "#2f6bd8", "#2fa35a", "#f4f3ef"
KEY, KEY_SH, PAD_SH = "#2a2a2a", "#0f0f0f", "#5e5f5b"
LEVELS = ["#ffd2bd", "#ffa070", "#ff7a3d", ORANGE]
OCTAVES = 3
BLACK = {1, 3, 6, 8, 10}
CYCLE = 9.0


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
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    current, best = streaks(days)
    langs = languages(user["repositories"]["nodes"], 1)
    preset = langs[0][0].upper() if langs else "INIT"
    notes = 12 * OCTAVES
    weeks = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]][-notes:]
    weeks = [0] * (notes - len(weeks)) + weeks
    ranked = sorted(weeks)
    peak = ranked[int(len(ranked) * 0.9)] or 1
    out = []
    a = out.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    a("<style>")
    a('text { font-family: "SF Mono", "Cascadia Code", Menlo, Consolas, "DejaVu Sans Mono", monospace; }')
    a(f".i {{ fill: {S_INK}; }} .d {{ fill: {S_DIM}; }} .o {{ fill: {ORANGE}; }} .b {{ font-weight: 700; }}")
    a(f".lbl {{ fill: {DIM_INK}; font-size: 8px; letter-spacing: 1px; }}")
    a("@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }")
    a(".blink { animation: blink 1s step-end infinite; }")
    a("@keyframes press { 0% { opacity: 0.55; } 6% { opacity: 0; } 100% { opacity: 0; } }")
    a(f".press {{ opacity: 0; animation: press {CYCLE}s linear infinite; }}")
    a("@keyframes wheel { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-14px); } }")
    a(".wheel { animation: wheel 4s ease-in-out infinite; }")
    a("</style>")
    a("<defs>")
    a(f'<linearGradient id="body" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a9aaa5"/><stop offset="1" stop-color="{BODY}"/></linearGradient>')
    a('<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0.07"/><stop offset="0.5" stop-color="#ffffff" stop-opacity="0"/></linearGradient>')
    a('<linearGradient id="ivory" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e4e3de"/><stop offset="0.15" stop-color="#f4f3ef"/><stop offset="1" stop-color="#ffffff"/></linearGradient>')
    a('<linearGradient id="ebony" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a1a1a"/><stop offset="1" stop-color="#3a3a3a"/></linearGradient>')
    a('<linearGradient id="roll" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1a1a1a"/><stop offset="0.5" stop-color="#4a4a4a"/><stop offset="1" stop-color="#1a1a1a"/></linearGradient>')
    a("</defs>")

    a(f'<rect x="4" y="10" width="{W - 8}" height="{H - 12}" rx="20" fill="{SIDE}"/>')
    a(f'<rect x="4" y="4" width="{W - 8}" height="{H - 14}" rx="20" fill="url(#body)" stroke="{EDGE}" stroke-width="1.5"/>')
    for x, y in [(20, 20), (W - 20, 20)]:
        a(f'<circle cx="{x}" cy="{y}" r="4" fill="{EDGE}"/><path d="M{x - 2.5} {y} h5" stroke="{DIM_INK}" stroke-width="1"/>')

    sx, sy, sw, sh = 150, 26, 300, 56
    a(f'<rect x="{sx - 7}" y="{sy - 7}" width="{sw + 14}" height="{sh + 14}" rx="9" fill="{KEY}"/>')
    a(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="4" fill="{SCREEN}"/>')
    a(f'<text x="{sx + 12}" y="{sy + 18}" font-size="9" class="o b">PRESET {preset}</text>')
    a(f'<text x="{sx + sw - 12}" y="{sy + 18}" font-size="9" text-anchor="end" class="d">STREAK {current}D  BEST {best}D</text>')
    a(f'<text x="{sx + 12}" y="{sy + 45}" font-size="22" class="i b">{cal["totalContributions"]}</text>')
    a(f'<text x="{sx + 12 + len(str(cal["totalContributions"])) * 14 + 6}" y="{sy + 45}" font-size="10" class="d">contributions in the last year<tspan class="o blink"> _</tspan></text>')
    a(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="4" fill="url(#glass)"/>')

    a(f'<text x="480" y="46" font-size="20" fill="{INK}" class="b">mello</text>')
    a(f'<text x="480" y="62" class="lbl">KEYS-{notes}  ·  ONE KEY PER WEEK</text>')
    for k, (c, name) in enumerate([(ORANGE, "REC"), (GREEN, "PLAY"), (KEY, "OCT")]):
        x = 680 + k * 34
        a(f'<rect x="{x}" y="{31 + 3}" width="26" height="22" rx="5" fill="{KEY_SH}"/>')
        a(f'<rect x="{x}" y="31" width="26" height="22" rx="5" fill="{KEY}"/>')
        if name == "REC":
            a(f'<circle cx="{x + 13}" cy="42" r="4.5" fill="{c}"/>')
        elif name == "PLAY":
            a(f'<path d="M{x + 10} 36 l8 6 l-8 6 z" fill="{c}"/>')
        else:
            a(f'<text x="{x + 13}" y="45" font-size="9" text-anchor="middle" fill="#e6e4de">+/-</text>')
        a(f'<text x="{x + 13}" y="68" text-anchor="middle" class="lbl" font-size="7">{name}</text>')

    for k, name in enumerate(["PITCH", "MOD"]):
        x = 36 + k * 46
        a(f'<rect x="{x}" y="104" width="28" height="110" rx="6" fill="{KEY_SH}"/>')
        a(f'<rect x="{x + 5}" y="110" width="18" height="98" rx="4" fill="url(#roll)"/>')
        cls = ' class="wheel"' if k == 1 else ""
        a(f'<g{cls}><rect x="{x + 5}" y="{153 if k == 0 else 175}" width="18" height="6" rx="1" fill="{ORANGE if k == 1 else "#8a8a86"}"/></g>')
        a(f'<text x="{x + 14}" y="230" text-anchor="middle" class="lbl" font-size="7">{name}</text>')

    kx, ky, kw = 140, 96, 646
    whites = [i for i in range(notes) if i % 12 not in BLACK]
    ww = kw / len(whites)
    wh, bh, bw = 132, 82, ww * 0.6
    a(f'<rect x="{kx - 6}" y="{ky - 6}" width="{kw + 12}" height="{wh + 12}" rx="6" fill="{KEY_SH}"/>')
    pos = {}
    for n, i in enumerate(whites):
        pos[i] = kx + n * ww
    for i in range(notes):
        if i % 12 in BLACK:
            pos[i] = pos[i - 1] + ww - bw / 2

    def key(i, x, w, h, base):
        count = weeks[i]
        lit = level(count, peak)
        a(f'<rect x="{x:.1f}" y="{ky}" width="{w:.1f}" height="{h}" rx="3" fill="{base}"><title>{count} contributions</title></rect>')
        if lit:
            inset = 3 if base == "url(#ebony)" else 0
            a(f'<rect x="{x + inset:.1f}" y="{ky + h * 0.55:.1f}" width="{w - 2 * inset:.1f}" height="{h * 0.45 - 3:.1f}" rx="3" fill="{lit}"/>')
        delay = i / notes * CYCLE
        a(f'<rect class="press" style="animation-delay: {delay:.2f}s" x="{x:.1f}" y="{ky}" width="{w:.1f}" height="{h}" rx="3" fill="{ORANGE}"/>')

    for i in whites:
        key(i, pos[i] + 1, ww - 2, wh, "url(#ivory)")
    for i in range(notes):
        if i % 12 in BLACK:
            a(f'<rect x="{pos[i]:.1f}" y="{ky}" width="{bw:.1f}" height="{bh + 3}" rx="3" fill="{KEY_SH}"/>')
            key(i, pos[i], bw, bh, "url(#ebony)")
    a(f'<rect x="{kx}" y="{ky - 1}" width="{kw}" height="4" fill="#c81e0a" opacity="0.8"/>')
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
