import datetime
import json
import math
import os
import random
import urllib.request

GITHUB_USER = "SachinMaurya24"
CF_HANDLE = "Borachii"
ATCODER_HANDLE = "Borachii"

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "panel": "#161b22",
        "border": "#30363d",
        "grid": "#21262d",
        "text": "#e6edf3",
        "muted": "#8b949e",
        "accent": "#58a6ff",
        "accent2": "#a371f7",
        "node": "#79c0ff",
    },
    "light": {
        "bg": "#fafaf9",
        "panel": "#ffffff",
        "border": "#d0d7de",
        "grid": "#eaeef2",
        "text": "#1f2328",
        "muted": "#57606a",
        "accent": "#0969da",
        "accent2": "#8250df",
        "node": "#0969da",
    },
}


def fetch_json(url, headers=None, payload=None):
    req_headers = {"User-Agent": "SachinMaurya24-Profile-Bot"}
    if headers:
        req_headers.update(headers)
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=req_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------
# 1. BARNES-HUT QUADTREE HEADER
# ---------------------------------------------------------
class QuadNode:
    def __init__(self, x, y, w, h, depth=0):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.depth = depth
        self.points = []
        self.children = []

    def subdivide(self, capacity=3, max_depth=6):
        if len(self.points) <= capacity or self.depth >= max_depth:
            return
        hw, hh = self.w / 2.0, self.h / 2.0
        quads = [
            QuadNode(self.x, self.y, hw, hh, self.depth + 1),
            QuadNode(self.x + hw, self.y, hw, hh, self.depth + 1),
            QuadNode(self.x, self.y + hh, hw, hh, self.depth + 1),
            QuadNode(self.x + hw, self.y + hh, hw, hh, self.depth + 1),
        ]
        for px, py in self.points:
            idx = (1 if px >= self.x + hw else 0) + (2 if py >= self.y + hh else 0)
            quads[idx].points.append((px, py))
        self.children = quads
        for q in self.children:
            q.subdivide(capacity, max_depth)

    def collect_cells(self, out):
        out.append((self.x, self.y, self.w, self.h, self.depth))
        for c in self.children:
            c.collect_cells(out)


def get_commit_points(width, height):
    token = os.environ.get("GITHUB_TOKEN")
    rng = random.Random(24)
    points = []

    if token:
        try:
            query = """
            query($login: String!) {
              user(login: $login) {
                contributionsCollection {
                  contributionCalendar {
                    weeks { contributionDays { contributionCount } }
                  }
                }
              }
            }
            """
            res = fetch_json(
                "https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                payload={"query": query, "variables": {"login": GITHUB_USER}},
            )
            weeks = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
            n_weeks = max(len(weeks), 1)
            for wi, week in enumerate(weeks):
                for di, day in enumerate(week["contributionDays"]):
                    count = min(day["contributionCount"], 6)
                    for _ in range(count):
                        px = (wi + rng.random()) / n_weeks * width
                        py = (di + rng.random()) / 7.0 * height
                        points.append((px, py))
        except Exception:
            points = []

    # Fallback: two colliding Gaussian clusters if API unavailable or sparse
    if len(points) < 40:
        for _ in range(90):
            cx, cy = (width * 0.22, height * 0.52) if rng.random() < 0.5 else (width * 0.78, height * 0.48)
            px = min(max(rng.gauss(cx, width * 0.09), 6), width - 6)
            py = min(max(rng.gauss(cy, height * 0.22), 6), height - 6)
            points.append((px, py))

    return points


def build_quadtree_svg(points, theme_name):
    t = THEMES[theme_name]
    w, h = 960, 220
    root = QuadNode(0, 0, w, h)
    root.points = points
    root.subdivide(capacity=3, max_depth=6)

    cells = []
    root.collect_cells(cells)

    rects = []
    for cx, cy, cw, ch, depth in cells:
        opacity = max(0.12, 0.55 - depth * 0.07)
        rects.append(
            f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{ch:.1f}" '
            f'fill="none" stroke="{t["accent"]}" stroke-opacity="{opacity:.2f}" stroke-width="0.7" />'
        )

    dots = [
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1.5" fill="{t["node"]}" fill-opacity="0.65" />'
        for px, py in points
    ]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%">
  <defs>
    <radialGradient id="title-fade-{theme_name}" cx="50%" cy="50%" r="48%">
      <stop offset="0%" stop-color="{t['bg']}" stop-opacity="0.94" />
      <stop offset="70%" stop-color="{t['bg']}" stop-opacity="0.72" />
      <stop offset="100%" stop-color="{t['bg']}" stop-opacity="0" />
    </radialGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="10" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1" />
  <g>{''.join(rects)}</g>
  <g>{''.join(dots)}</g>
  <rect x="200" y="34" width="560" height="152" rx="12" fill="url(#title-fade-{theme_name})" />
  <text x="480" y="98" text-anchor="middle" fill="{t['text']}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="34" font-weight="700" letter-spacing="4">SACHIN MAURYA</text>
  <text x="480" y="128" text-anchor="middle" fill="{t['muted']}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12.5" letter-spacing="1.5">C++20 SYSTEMS  ·  PHYSICS SIMULATIONS  ·  QUANTITATIVE MODELING</text>
  <text x="480" y="156" text-anchor="middle" fill="{t['accent']}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" letter-spacing="1">FIG. 01 — BARNES-HUT QUADTREE SUBDIVISION · N = {len(points)} COMMIT NODES · θ = 0.5</text>
</svg>
"""


# ---------------------------------------------------------
# 2. QUANT-STYLE CP TELEMETRY SVG
# ---------------------------------------------------------
def get_cf_ratings(handle):
    try:
        res = fetch_json(f"https://codeforces.com/api/user.rating?handle={handle}")
        if res.get("status") == "OK":
            return [int(item["newRating"]) for item in res["result"]]
    except Exception:
        pass
    return []


def get_atcoder_ratings(handle):
    try:
        res = fetch_json(f"https://atcoder.jp/users/{handle}/history/json")
        return [int(item["NewRating"]) for item in res if item.get("IsRated")]
    except Exception:
        pass
    return []


def compute_quant_metrics(ratings):
    if not ratings:
        return {"cur": "—", "peak": "—", "mu": "—", "sigma": "—", "mdd": "—"}
    cur = ratings[-1]
    peak = max(ratings)
    deltas = [ratings[i] - ratings[i - 1] for i in range(1, len(ratings))]
    if deltas:
        mu = sum(deltas) / len(deltas)
        var = sum((d - mu) ** 2 for d in deltas) / len(deltas)
        sigma = math.sqrt(var)
    else:
        mu, sigma = 0.0, 0.0

    running_peak = ratings[0]
    mdd = 0
    for r in ratings:
        running_peak = max(running_peak, r)
        mdd = max(mdd, running_peak - r)

    return {
        "cur": str(cur),
        "peak": str(peak),
        "mu": f"{mu:+.1f}",
        "sigma": f"{sigma:.1f}",
        "mdd": f"-{mdd}",
    }


def render_panel(title, handle, ratings, x0, y0, pw, ph, stroke_color, t):
    stats = compute_quant_metrics(ratings)
    px, py, plot_w, plot_h = x0 + 24, y0 + 62, pw - 48, 86

    grid_lines = []
    for i in range(4):
        gy = py + i * (plot_h / 3.0)
        grid_lines.append(
            f'<line x1="{px}" y1="{gy:.1f}" x2="{px + plot_w}" y2="{gy:.1f}" '
            f'stroke="{t["grid"]}" stroke-width="1" stroke-dasharray="3,3" />'
        )

    series_svg = ""
    if len(ratings) >= 2:
        r_min, r_max = min(ratings), max(ratings)
        span = max(r_max - r_min, 1)
        pts = []
        for idx, r in enumerate(ratings):
            sx = px + (idx / (len(ratings) - 1)) * plot_w
            sy = py + plot_h - ((r - r_min) / span) * plot_h
            pts.append((sx, sy))
        poly_str = " ".join(f"{sx:.1f},{sy:.1f}" for sx, sy in pts)
        area_str = f"{px:.1f},{py + plot_h:.1f} {poly_str} {px + plot_w:.1f},{py + plot_h:.1f}"
        last_x, last_y = pts[-1]
        series_svg = (
            f'<polygon points="{area_str}" fill="{stroke_color}" fill-opacity="0.12" />'
            f'<polyline points="{poly_str}" fill="none" stroke="{stroke_color}" stroke-width="2" />'
            f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="3.5" fill="{stroke_color}" />'
        )
    elif len(ratings) == 1:
        series_svg = f'<circle cx="{px + plot_w / 2:.1f}" cy="{py + plot_h / 2:.1f}" r="4" fill="{stroke_color}" />'
    else:
        series_svg = (
            f'<text x="{px + plot_w / 2:.1f}" y="{py + plot_h / 2:.1f}" text-anchor="middle" '
            f'fill="{t["muted"]}" font-size="11" font-family="ui-monospace, monospace">No rated contests found</text>'
        )

    return f"""
  <g>
    <rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" rx="8" fill="{t['panel']}" stroke="{t['border']}" stroke-width="1" />
    <text x="{x0 + 24}" y="{y0 + 30}" fill="{t['text']}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="700">{title}</text>
    <text x="{x0 + pw - 24}" y="{y0 + 30}" text-anchor="end" fill="{stroke_color}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12">@{handle}  ·  n={len(ratings)}</text>
    <text x="{x0 + 24}" y="{y0 + 48}" fill="{t['muted']}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">RATING {stats['cur']}   |   PEAK {stats['peak']}</text>
    {''.join(grid_lines)}
    {series_svg}
    <line x1="{x0 + 24}" y1="{y0 + 166}" x2="{x0 + pw - 24}" y2="{y0 + 166}" stroke="{t['grid']}" stroke-width="1" />
    <text x="{x0 + 24}" y="{y0 + 188}" fill="{t['muted']}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">μ(Δr): <tspan fill="{t['text']}" font-weight="600">{stats['mu']}</tspan></text>
    <text x="{x0 + pw / 2:.1f}" y="{y0 + 188}" text-anchor="middle" fill="{t['muted']}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">σ(Δr): <tspan fill="{t['text']}" font-weight="600">{stats['sigma']}</tspan></text>
    <text x="{x0 + pw - 24}" y="{y0 + 188}" text-anchor="end" fill="{t['muted']}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">MAX DD: <tspan fill="{t['text']}" font-weight="600">{stats['mdd']}</tspan></text>
  </g>"""


def build_telemetry_svg(cf_ratings, ac_ratings, theme_name):
    t = THEMES[theme_name]
    w, h = 960, 250
    updated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d UTC")
    left = render_panel("CODEFORCES SERIES", CF_HANDLE, cf_ratings, 16, 36, 456, 200, t["accent"], t)
    right = render_panel("ATCODER SERIES", ATCODER_HANDLE, ac_ratings, 488, 36, 456, 200, t["accent2"], t)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%">
  <rect width="{w}" height="{h}" rx="10" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1" />
  <text x="20" y="23" fill="{t['muted']}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" letter-spacing="1">FIG. 02 — COMPETITIVE PROGRAMMING TIME-SERIES TELEMETRY</text>
  <text x="{w - 20}" y="23" text-anchor="end" fill="{t['muted']}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">UPDATED {updated}</text>
  {left}
  {right}
</svg>
"""


def main():
    os.makedirs("assets", exist_ok=True)
    points = get_commit_points(960, 220)
    cf_ratings = get_cf_ratings(CF_HANDLE)
    ac_ratings = get_atcoder_ratings(ATCODER_HANDLE)

    for theme in ("dark", "light"):
        with open(f"assets/quadtree-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(build_quadtree_svg(points, theme))
        with open(f"assets/cp-telemetry-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(build_telemetry_svg(cf_ratings, ac_ratings, theme))


if __name__ == "__main__":
    main()
