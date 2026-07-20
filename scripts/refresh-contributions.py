#!/usr/bin/env python3
"""
Refresh assets/contribution-comet.svg with the latest REAL contribution data.

Usage:
    python scripts/refresh-contributions.py [github-username]

Requires the GitHub CLI (`gh`) to be installed and authenticated (`gh auth login`).
Default username: XoAuraHiru. Run it whenever you want the starfield up to date.
"""
import json, subprocess, sys, datetime
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "XoAuraHiru"
OUT = Path(__file__).resolve().parent.parent / "assets" / "contribution-comet.svg"

QUERY = (
    "query($login:String!){ user(login:$login){ contributionsCollection{"
    " contributionCalendar{ totalContributions weeks{ contributionDays{"
    " date contributionCount weekday contributionLevel } } } } } }"
)

def fetch(login):
    try:
        res = subprocess.run(
            ["gh", "api", "graphql", "-f", f"login={login}", "-f", f"query={QUERY}"],
            capture_output=True, text=True, shell=(sys.platform == "win32"),
        )
    except FileNotFoundError:
        sys.exit("error: GitHub CLI (`gh`) not found. Install it: https://cli.github.com")
    if res.returncode != 0:
        sys.exit(f"error: gh api failed. Run `gh auth login` first.\n{res.stderr.strip()}")
    return json.loads(res.stdout)["data"]["user"]["contributionsCollection"]["contributionCalendar"]

# ── geometry & palette ────────────────────────────────────
CELL, GAP = 11, 3
PITCH = CELL + GAP
X0, Y0 = 34, 26
LVL = {
    "NONE": "#191233", "FIRST_QUARTILE": "#512c8f", "SECOND_QUARTILE": "#7c3aed",
    "THIRD_QUARTILE": "#a855f7", "FOURTH_QUARTILE": "#22d3ee",
}
HOT = {"THIRD_QUARTILE", "FOURTH_QUARTILE"}
MONTHS = ["", "Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def build_svg(cal):
    weeks, total = cal["weeks"], cal["totalContributions"]
    COLS = len(weeks)
    GRID_W = COLS * PITCH
    W = X0 + GRID_W + 12
    H = Y0 + 7 * PITCH + 44

    cells, months, last_m = [], [], None
    for i, wk in enumerate(weeks):
        days = wk["contributionDays"]
        m = datetime.date.fromisoformat(days[0]["date"]).month
        if m != last_m and 0 <= i <= COLS - 2:
            months.append((X0 + i * PITCH, MONTHS[m]))
            last_m = m
        for d in days:
            wd, lvl, cnt = d["weekday"], d["contributionLevel"], d["contributionCount"]
            x, y = X0 + i * PITCH, Y0 + wd * PITCH
            delay = round(i * 0.028 + wd * 0.006, 3)
            cls = "cell hot" if lvl in HOT else "cell"
            flt = ' filter="url(#cellglow)"' if lvl == "FOURTH_QUARTILE" else ""
            tw = f' style="--d:{delay}s;--t:{round((i*7+wd)%5*0.6+2.0,2)}s"'
            cells.append(
                f'<rect class="{cls}"{tw} x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" fill="{LVL[lvl]}"{flt}><title>{d["date"]}: {cnt} '
                f'contribution{"s" if cnt != 1 else ""}</title></rect>'
            )

    clean = []
    for mx, mt in months:
        if clean and mx - clean[-1][0] < PITCH * 1.6:
            continue
        clean.append((mx, mt))
    month_svg = "".join(f'<text x="{mx}" y="16" class="mlabel">{mt}</text>' for mx, mt in clean)
    wd_svg = "".join(
        f'<text x="10" y="{Y0 + r*PITCH + CELL - 2}" class="wlabel">{lbl}</text>'
        for r, lbl in [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    )
    lx = W - 190
    legend_cells = "".join(
        f'<rect x="{lx + 34 + k*16}" y="{H-20}" width="11" height="11" rx="2.5" fill="{LVL[l]}"/>'
        for k, l in enumerate(["NONE","FIRST_QUARTILE","SECOND_QUARTILE","THIRD_QUARTILE","FOURTH_QUARTILE"])
    )
    legend = (f'<text x="{lx}" y="{H-11}" class="legend">Less</text>{legend_cells}'
              f'<text x="{lx + 34 + 5*16 + 4}" y="{H-11}" class="legend">More</text>')
    cex, cey = X0 + GRID_W - 6, Y0 + 7*PITCH - 12

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{USER}'s GitHub contribution graph — {total} contributions in the last year, rendered as a cosmic starfield">
  <title>{total} contributions in the last year</title>
  <defs>
    <linearGradient id="cbg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0b0620"/><stop offset="0.55" stop-color="#140a2c"/><stop offset="1" stop-color="#05030f"/>
    </linearGradient>
    <radialGradient id="cneb" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#7c3aed" stop-opacity="0.35"/><stop offset="1" stop-color="#7c3aed" stop-opacity="0"/></radialGradient>
    <radialGradient id="cneb2" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#06b6d4" stop-opacity="0.30"/><stop offset="1" stop-color="#06b6d4" stop-opacity="0"/></radialGradient>
    <linearGradient id="ctrail" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#a5f3fc" stop-opacity="0"/><stop offset="1" stop-color="#ffffff"/></linearGradient>
    <filter id="cellglow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="cheadglow" x="-120%" y="-120%" width="340%" height="340%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <clipPath id="cframe"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16"/></clipPath>
  </defs>
  <style>
    @keyframes pop    {{ 0%{{opacity:0;transform:scale(0)}} 70%{{opacity:1;transform:scale(1.18)}} 100%{{opacity:1;transform:scale(1)}} }}
    @keyframes twk    {{ 0%,100%{{opacity:1}} 50%{{opacity:.55}} }}
    @keyframes csweep {{ 0%{{opacity:0;transform:translate(-30px,-14px)}} 4%{{opacity:1}} 15%{{opacity:1}} 22%{{opacity:0;transform:translate({cex}px,{cey}px)}} 100%{{opacity:0;transform:translate({cex}px,{cey}px)}} }}
    @keyframes nebpulse{{ 0%,100%{{opacity:.7}} 50%{{opacity:1}} }}
    .cell   {{ transform-box:fill-box; transform-origin:center; animation:pop .55s cubic-bezier(.2,.7,.3,1.4) var(--d) both }}
    .hot    {{ animation:pop .55s cubic-bezier(.2,.7,.3,1.4) var(--d) both, twk var(--t) ease-in-out 1.8s infinite }}
    .comet  {{ animation:csweep 6.5s ease-in 1.2s infinite }}
    .neb    {{ animation:nebpulse 11s ease-in-out infinite }}
    .mlabel {{ fill:#9a8cc4; font:600 10px ui-monospace,'Cascadia Code',Consolas,monospace }}
    .wlabel {{ fill:#9a8cc4; font:600 9px ui-monospace,'Cascadia Code',Consolas,monospace }}
    .legend {{ fill:#9a8cc4; font:600 10px ui-monospace,'Cascadia Code',Consolas,monospace }}
    .total  {{ fill:#c4b5fd; font:700 13px 'Segoe UI',system-ui,Arial,sans-serif }}
    .totacc {{ fill:#22d3ee }}
    @media (prefers-reduced-motion: reduce){{ .cell,.hot{{animation:pop .01s linear both}} .comet{{display:none}} .neb{{animation:none}} }}
  </style>
  <g clip-path="url(#cframe)">
    <rect x="1" y="1" width="{W-2}" height="{H-2}" fill="url(#cbg)"/>
    <ellipse class="neb" style="animation-delay:0s"  cx="{W-90}" cy="20"  rx="220" ry="130" fill="url(#cneb)"/>
    <ellipse class="neb" style="animation-delay:-5s" cx="70" cy="{H-20}" rx="200" ry="120" fill="url(#cneb2)"/>
    <g fill="#cbd5ff" opacity="0.5">
      <circle cx="{W-30}" cy="12" r="0.9"/><circle cx="{W-60}" cy="{H-14}" r="0.8"/>
      <circle cx="20" cy="18" r="0.8"/><circle cx="{W-16}" cy="{H//2}" r="0.9"/><circle cx="12" cy="{H-30}" r="0.7"/>
    </g>
    {month_svg}
    {wd_svg}
    <g>{''.join(cells)}</g>
    {legend}
    <text x="{X0}" y="{H-9}" class="total">&#10022; <tspan class="totacc">{total:,}</tspan> contributions in the last year</text>
    <g class="comet">
      <line x1="0" y1="0" x2="-44" y2="-7" stroke="url(#ctrail)" stroke-width="2.4" stroke-linecap="round"/>
      <circle r="2.6" fill="#ffffff" filter="url(#cheadglow)"/>
    </g>
    <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="15" fill="none" stroke="#4c1d95" stroke-opacity="0.5" stroke-width="1.5"/>
  </g>
</svg>
'''

if __name__ == "__main__":
    cal = fetch(USER)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_svg(cal), encoding="utf-8")
    print(f"Updated {OUT} - {cal['totalContributions']:,} contributions for @{USER}")
