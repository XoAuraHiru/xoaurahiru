#!/usr/bin/env python3
"""
Refresh Hirun's profile metrics from REAL GitHub data — no third-party services.

Regenerates two self-contained animated SVGs from live data:
  * assets/contribution-comet.svg  — a year of contributions as a starfield
  * assets/github-signal.svg       — stat tiles + a language spectrum across every repo

Usage:
    python scripts/refresh-metrics.py [github-username]

Requires the GitHub CLI (`gh`) installed and authenticated (`gh auth login`).
Default username: XoAuraHiru.
"""
import json, subprocess, sys, datetime, collections
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "XoAuraHiru"
ASSETS = Path(__file__).resolve().parent.parent / "assets"

QUERY = (
    "query($login:String!){ user(login:$login){ login name"
    " followers{totalCount} following{totalCount}"
    " contributionsCollection{ totalCommitContributions totalPullRequestContributions"
    " contributionCalendar{ totalContributions weeks{ contributionDays{"
    " date contributionCount weekday contributionLevel } } } }"
    " repositories(first:100, ownerAffiliations:OWNER, isFork:false,"
    " orderBy:{field:STARGAZERS, direction:DESC}){ totalCount nodes{ stargazerCount"
    " languages(first:20, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name color } } } } } } }"
)

# ── cosmic palette (shared) ───────────────────────────────
BG_STOPS = '<stop offset="0" stop-color="#0b0620"/><stop offset="0.55" stop-color="#140a2c"/><stop offset="1" stop-color="#05030f"/>'
INK, MUTED, ACCENT = "#d6ccf5", "#9a8cc4", "#22d3ee"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fetch(login):
    try:
        res = subprocess.run(
            ["gh", "api", "graphql", "-f", f"login={login}", "-f", f"query={QUERY}"],
            capture_output=True, text=True, shell=(sys.platform == "win32"),
        )
    except FileNotFoundError:
        sys.exit("error: GitHub CLI (`gh`) not found — https://cli.github.com")
    if res.returncode != 0:
        sys.exit(f"error: gh api failed. Run `gh auth login` first.\n{res.stderr.strip()}")
    return json.loads(res.stdout)["data"]["user"]


# ══════════════════════════════════════════════════════════
#  Contribution starfield  (assets/contribution-comet.svg)
# ══════════════════════════════════════════════════════════
CELL, GAP = 11, 3
PITCH = CELL + GAP
CX0, CY0 = 34, 26
LVL = {"NONE": "#191233", "FIRST_QUARTILE": "#512c8f", "SECOND_QUARTILE": "#7c3aed",
       "THIRD_QUARTILE": "#a855f7", "FOURTH_QUARTILE": "#22d3ee"}
HOT = {"THIRD_QUARTILE", "FOURTH_QUARTILE"}
MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def build_contrib(cal):
    weeks, total = cal["weeks"], cal["totalContributions"]
    cols = len(weeks)
    gw = cols * PITCH
    W = CX0 + gw + 12
    H = CY0 + 7 * PITCH + 44
    cells, months, last_m = [], [], None
    for i, wk in enumerate(weeks):
        days = wk["contributionDays"]
        m = datetime.date.fromisoformat(days[0]["date"]).month
        if m != last_m and 0 <= i <= cols - 2:
            months.append((CX0 + i * PITCH, MONTHS[m])); last_m = m
        for d in days:
            wd, lvl, cnt = d["weekday"], d["contributionLevel"], d["contributionCount"]
            x, y = CX0 + i * PITCH, CY0 + wd * PITCH
            delay = round(i * 0.028 + wd * 0.006, 3)
            cls = "cell hot" if lvl in HOT else "cell"
            flt = ' filter="url(#cellglow)"' if lvl == "FOURTH_QUARTILE" else ""
            st = f' style="--d:{delay}s;--t:{round((i*7+wd)%5*0.6+2.0,2)}s"'
            cells.append(f'<rect class="{cls}"{st} x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                         f'rx="2.5" fill="{LVL[lvl]}"{flt}><title>{d["date"]}: {cnt} '
                         f'contribution{"s" if cnt != 1 else ""}</title></rect>')
    clean = []
    for mx, mt in months:
        if clean and mx - clean[-1][0] < PITCH * 1.6:
            continue
        clean.append((mx, mt))
    month_svg = "".join(f'<text x="{mx}" y="16" class="mlabel">{mt}</text>' for mx, mt in clean)
    wd_svg = "".join(f'<text x="10" y="{CY0 + r*PITCH + CELL - 2}" class="wlabel">{lbl}</text>'
                     for r, lbl in [(1, "Mon"), (3, "Wed"), (5, "Fri")])
    lx = W - 190
    legend_cells = "".join(f'<rect x="{lx + 34 + k*16}" y="{H-20}" width="11" height="11" rx="2.5" fill="{LVL[l]}"/>'
                           for k, l in enumerate(["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]))
    legend = (f'<text x="{lx}" y="{H-11}" class="legend">Less</text>{legend_cells}'
              f'<text x="{lx + 34 + 5*16 + 4}" y="{H-11}" class="legend">More</text>')
    cex, cey = CX0 + gw - 6, CY0 + 7 * PITCH - 12
    style = """
    @keyframes pop    { 0%{opacity:0;transform:scale(0)} 70%{opacity:1;transform:scale(1.18)} 100%{opacity:1;transform:scale(1)} }
    @keyframes twk    { 0%,100%{opacity:1} 50%{opacity:.55} }
    @keyframes csweep { 0%{opacity:0;transform:translate(-30px,-14px)} 4%{opacity:1} 15%{opacity:1} 22%{opacity:0;transform:translate(CEXpx,CEYpx)} 100%{opacity:0;transform:translate(CEXpx,CEYpx)} }
    @keyframes nebpulse{ 0%,100%{opacity:.7} 50%{opacity:1} }
    .cell   { transform-box:fill-box; transform-origin:center; animation:pop .55s cubic-bezier(.2,.7,.3,1.4) var(--d) both }
    .hot    { animation:pop .55s cubic-bezier(.2,.7,.3,1.4) var(--d) both, twk var(--t) ease-in-out 1.8s infinite }
    .comet  { animation:csweep 6.5s ease-in 1.2s infinite }
    .neb    { animation:nebpulse 11s ease-in-out infinite }
    .mlabel { fill:#9a8cc4; font:600 10px ui-monospace,'Cascadia Code',Consolas,monospace }
    .wlabel { fill:#9a8cc4; font:600 9px ui-monospace,'Cascadia Code',Consolas,monospace }
    .legend { fill:#9a8cc4; font:600 10px ui-monospace,'Cascadia Code',Consolas,monospace }
    .total  { fill:#c4b5fd; font:700 13px 'Segoe UI',system-ui,Arial,sans-serif }
    .totacc { fill:#22d3ee }
    @media (prefers-reduced-motion: reduce){ .cell,.hot{animation:pop .01s linear both} .comet{display:none} .neb{animation:none} }
    """.replace("CEX", str(cex)).replace("CEY", str(cey))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{USER}'s GitHub contribution graph — {total} contributions in the last year, rendered as a cosmic starfield">
  <title>{total} contributions in the last year</title>
  <defs>
    <linearGradient id="cbg" x1="0" y1="0" x2="1" y2="1">{BG_STOPS}</linearGradient>
    <radialGradient id="cneb" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#7c3aed" stop-opacity="0.35"/><stop offset="1" stop-color="#7c3aed" stop-opacity="0"/></radialGradient>
    <radialGradient id="cneb2" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#06b6d4" stop-opacity="0.30"/><stop offset="1" stop-color="#06b6d4" stop-opacity="0"/></radialGradient>
    <linearGradient id="ctrail" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#a5f3fc" stop-opacity="0"/><stop offset="1" stop-color="#ffffff"/></linearGradient>
    <filter id="cellglow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="cheadglow" x="-120%" y="-120%" width="340%" height="340%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <clipPath id="cframe"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16"/></clipPath>
  </defs>
  <style>{style}</style>
  <g clip-path="url(#cframe)">
    <rect x="1" y="1" width="{W-2}" height="{H-2}" fill="url(#cbg)"/>
    <ellipse class="neb" style="animation-delay:0s"  cx="{W-90}" cy="20"  rx="220" ry="130" fill="url(#cneb)"/>
    <ellipse class="neb" style="animation-delay:-5s" cx="70" cy="{H-20}" rx="200" ry="120" fill="url(#cneb2)"/>
    <g fill="#cbd5ff" opacity="0.5"><circle cx="{W-30}" cy="12" r="0.9"/><circle cx="{W-60}" cy="{H-14}" r="0.8"/><circle cx="20" cy="18" r="0.8"/><circle cx="{W-16}" cy="{H//2}" r="0.9"/><circle cx="12" cy="{H-30}" r="0.7"/></g>
    {month_svg}{wd_svg}
    <g>{''.join(cells)}</g>
    {legend}
    <text x="{CX0}" y="{H-9}" class="total">&#10022; <tspan class="totacc">{total:,}</tspan> contributions in the last year</text>
    <g class="comet"><line x1="0" y1="0" x2="-44" y2="-7" stroke="url(#ctrail)" stroke-width="2.4" stroke-linecap="round"/><circle r="2.6" fill="#ffffff" filter="url(#cheadglow)"/></g>
    <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="15" fill="none" stroke="#4c1d95" stroke-opacity="0.5" stroke-width="1.5"/>
  </g>
</svg>
'''


# ══════════════════════════════════════════════════════════
#  GitHub Signal  (assets/github-signal.svg)
# ══════════════════════════════════════════════════════════
W = 840
P = 24


def longest_streak(cal):
    days = sorted((d for wk in cal["weeks"] for d in wk["contributionDays"]), key=lambda d: d["date"])
    best = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        best = max(best, run)
    return best


def tile_icon(kind, cx, cy, color):
    if kind == "repo":
        return (f'<g stroke="{color}" stroke-width="1.6" fill="none">'
                f'<rect x="{cx-8}" y="{cy-5}" width="13" height="10" rx="2"/>'
                f'<rect x="{cx-5}" y="{cy-8}" width="13" height="10" rx="2" fill="#0b0620"/></g>')
    if kind == "contrib":
        return "".join(f'<rect x="{cx-9+k*7}" y="{cy-3}" width="5" height="6" rx="1.4" fill="{color}"/>' for k in range(3))
    if kind == "commit":
        return (f'<g stroke="{color}" stroke-width="1.6"><line x1="{cx-9}" y1="{cy}" x2="{cx+9}" y2="{cy}"/>'
                f'<circle cx="{cx}" cy="{cy}" r="3.4" fill="#0b0620"/></g>')
    if kind == "streak":
        return (f'<path transform="translate({cx},{cy})" d="M0,-8 C4,-3 6,-1 3.4,3.4 C2,5.4 -2,5.4 -3.4,3.4 '
                f'C-6,-1 -3.6,-3 0,-8 Z" fill="{color}"/>')
    if kind == "lang":
        return f'<text x="{cx}" y="{cy+4}" text-anchor="middle" style="fill:{color};font:800 14px ui-monospace,Consolas,monospace">&lt;/&gt;</text>'
    return ""


def build_signal(user):
    repos = user["repositories"]["nodes"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    n_repos = user["repositories"]["totalCount"]
    contribs = cal["totalContributions"]
    commits = user["contributionsCollection"]["totalCommitContributions"]

    lang = collections.defaultdict(lambda: [0, None])
    for r in repos:
        for e in r["languages"]["edges"]:
            lang[e["node"]["name"]][0] += e["size"]
            lang[e["node"]["name"]][1] = e["node"]["color"] or "#8b7fb0"
    n_lang = len(lang)
    tot = sum(v[0] for v in lang.values()) or 1
    ranked = sorted(lang.items(), key=lambda kv: -kv[1][0])
    display = [(n, 100 * s / tot, c) for n, (s, c) in ranked[:9]]
    if n_lang > 9:
        rest = sum(s for _, (s, c) in ranked[9:])
        display.append((f"+{n_lang - 9} more", 100 * rest / tot, "#8b7fb0"))
    maxshare = display[0][1] if display else 1

    tiles = [
        ("repo",    n_repos,  "Repositories",      "#22d3ee"),
        ("contrib", contribs, "Contributions 1y",  "#a855f7"),
        ("commit",  commits,  "Commits 1y",        "#38bdf8"),
        ("streak",  longest_streak(cal), "Longest streak", "#fb923c"),
        ("lang",    n_lang,   "Languages",         "#f472b6"),
    ]
    # ── stat tiles ──
    y0 = 22
    TH = 90
    G = 14
    TW = (W - 2 * P - (len(tiles) - 1) * G) / len(tiles)
    tsvg = []
    for i, (icon, val, label, acc) in enumerate(tiles):
        tx = P + i * (TW + G)
        cx = tx + TW / 2
        tsvg.append(
            f'<g class="tile" style="--d:{round(i*0.09,2)}s">'
            f'<rect x="{tx:.1f}" y="{y0}" width="{TW:.1f}" height="{TH}" rx="12" fill="#160c33" stroke="#3a2870" stroke-opacity="0.8"/>'
            f'{tile_icon(icon, cx, y0+24, acc)}'
            f'<text x="{cx:.1f}" y="{y0+60}" text-anchor="middle" class="num" style="fill:{acc}">{val:,}</text>'
            f'<text x="{cx:.1f}" y="{y0+78}" text-anchor="middle" class="tlabel">{esc(label)}</text>'
            f'</g>')

    # ── language spectrum ──
    ly = y0 + TH + 30
    by = ly + 22
    RH = 32
    colx = [P, P + (W - 2 * P) / 2 + 8]
    CW = (W - 2 * P - 16) / 2
    rows = []
    for idx, (name, pct, color) in enumerate(display):
        c, r = idx // 5, idx % 5
        x = colx[c]
        y = by + r * RH
        w = max(3, CW * (pct / maxshare))
        rows.append(
            f'<circle cx="{x+4:.1f}" cy="{y+5}" r="4.5" fill="{color}"/>'
            f'<text x="{x+16:.1f}" y="{y+9}" class="lname">{esc(name)}</text>'
            f'<text x="{x+CW:.1f}" y="{y+9}" text-anchor="end" class="lpct">{pct:.1f}%</text>'
            f'<rect x="{x:.1f}" y="{y+15}" width="{CW:.1f}" height="7" rx="3.5" fill="#241640"/>'
            f'<rect class="lbar" style="--d:{round(0.3+idx*0.07,2)}s" x="{x:.1f}" y="{y+15}" width="{w:.1f}" height="7" rx="3.5" fill="{color}"/>')

    H = by + 5 * RH + 20
    style = """
    @keyframes rise  { from{opacity:0;transform:translateY(10px) scale(.96)} to{opacity:1;transform:translateY(0) scale(1)} }
    @keyframes grow  { from{transform:scaleX(0)} to{transform:scaleX(1)} }
    @keyframes neb   { 0%,100%{opacity:.65} 50%{opacity:1} }
    .tile  { transform-box:fill-box; transform-origin:center; animation:rise .55s cubic-bezier(.2,.7,.3,1.2) var(--d) both }
    .lbar  { transform-box:fill-box; transform-origin:left center; animation:grow .9s cubic-bezier(.2,.7,.25,1) var(--d) both }
    .neb   { animation:neb 11s ease-in-out infinite }
    .num    { font:800 26px 'Segoe UI',system-ui,Arial,sans-serif }
    .tlabel { fill:#9a8cc4; font:600 10.5px ui-monospace,'Cascadia Code',Consolas,monospace }
    .eyebrow{ fill:#67e8f9; font:700 12px ui-monospace,'Cascadia Code',Consolas,monospace; letter-spacing:2px }
    .caption{ fill:#9a8cc4; font:600 11px ui-monospace,'Cascadia Code',Consolas,monospace }
    .lname  { fill:#d6ccf5; font:600 12.5px ui-monospace,'Cascadia Code',Consolas,monospace }
    .lpct   { fill:#9a8cc4; font:700 12px ui-monospace,'Cascadia Code',Consolas,monospace }
    @media (prefers-reduced-motion: reduce){ .tile{animation:rise .01s both} .lbar{animation:grow .01s both} .neb{animation:none} }
    """
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{USER}'s GitHub metrics: {n_repos} repositories, {contribs} contributions and {commits} commits in the last year, across {n_lang} languages led by {display[0][0]}">
  <title>{USER} — GitHub metrics and language spectrum</title>
  <defs>
    <linearGradient id="sbg" x1="0" y1="0" x2="1" y2="1">{BG_STOPS}</linearGradient>
    <radialGradient id="sneb" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#7c3aed" stop-opacity="0.30"/><stop offset="1" stop-color="#7c3aed" stop-opacity="0"/></radialGradient>
    <radialGradient id="sneb2" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#06b6d4" stop-opacity="0.26"/><stop offset="1" stop-color="#06b6d4" stop-opacity="0"/></radialGradient>
    <linearGradient id="srule" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#a855f7" stop-opacity="0"/></linearGradient>
    <clipPath id="sframe"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18"/></clipPath>
  </defs>
  <style>{style}</style>
  <g clip-path="url(#sframe)">
    <rect x="1" y="1" width="{W-2}" height="{H-2}" fill="url(#sbg)"/>
    <ellipse class="neb" cx="{W-70}" cy="10" rx="240" ry="150" fill="url(#sneb)"/>
    <ellipse class="neb" style="animation-delay:-5s" cx="40" cy="{H}" rx="220" ry="140" fill="url(#sneb2)"/>
    <g fill="#cbd5ff" opacity="0.45"><circle cx="{W-24}" cy="16" r="0.9"/><circle cx="30" cy="{H-18}" r="0.8"/><circle cx="{W-40}" cy="{H-24}" r="0.7"/><circle cx="18" cy="30" r="0.7"/></g>
    {''.join(tsvg)}
    <text x="{P}" y="{ly}" class="eyebrow">LANGUAGE SPECTRUM</text>
    <text x="{W-P}" y="{ly}" text-anchor="end" class="caption">{n_lang} languages &#183; {n_repos} repositories</text>
    <rect x="{P}" y="{ly+8}" width="168" height="2.5" rx="1.25" fill="url(#srule)"/>
    {''.join(rows)}
    <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="17" fill="none" stroke="#4c1d95" stroke-opacity="0.5" stroke-width="1.5"/>
  </g>
</svg>
'''


if __name__ == "__main__":
    u = fetch(USER)
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "contribution-comet.svg").write_text(
        build_contrib(u["contributionsCollection"]["contributionCalendar"]), encoding="utf-8")
    (ASSETS / "github-signal.svg").write_text(build_signal(u), encoding="utf-8")
    cal = u["contributionsCollection"]["contributionCalendar"]
    print(f"Updated assets for @{USER}: {u['repositories']['totalCount']} repos, "
          f"{cal['totalContributions']:,} contributions, "
          f"{u['contributionsCollection']['totalCommitContributions']} commits.")
