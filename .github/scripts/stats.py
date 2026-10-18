"""Render assets/stats.svg from public GitHub data. Needs `gh` + GH_TOKEN. Public data only, so local and CI output match."""
import json, os, subprocess, sys
from html import escape

USER = os.environ.get("GITHUB_USER") or sys.argv[1]
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "stats.svg")
COLORS = {"Shell": "#89e051", "JavaScript": "#f1e05a", "Python": "#3572A5", "C": "#555555", "C++": "#f34b7d",
          "Java": "#b07219", "HTML": "#e34c26", "CSS": "#563d7c", "Jupyter Notebook": "#DA5B0B", "TypeScript": "#3178c6"}

def gh(*args):
    return json.loads(subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout)

q = """query($u:String!){user(login:$u){followers{totalCount}
 repositories(privacy:PUBLIC,ownerAffiliations:OWNER,isFork:false,first:100){totalCount nodes{name stargazerCount}}
 contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions}}}"""
u = gh("api", "graphql", "-f", f"query={q}", "-F", f"u={USER}")["data"]["user"]
repos = u["repositories"]["nodes"]
stars = sum(r["stargazerCount"] for r in repos)
langs = {}
for r in repos:
    for k, v in gh("api", f"repos/{USER}/{r['name']}/languages").items():
        langs[k] = langs.get(k, 0) + v
total = sum(langs.values()) or 1
top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
cc = u["contributionsCollection"]
tiles = [("PUBLIC REPOS", u["repositories"]["totalCount"]), ("STARS", stars),
         ("COMMITS · 12 MO", cc["totalCommitContributions"]), ("PULL REQUESTS", cc["totalPullRequestContributions"])]

W, H = 900, 250
FONT = "ui-monospace,'JetBrains Mono','SFMono-Regular',Menlo,Consolas,monospace"
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
     f'<rect width="{W}" height="{H}" rx="14" fill="#0d1117"/>',
     '<text x="30" y="38" fill="#c9d1d9" font-size="16" font-weight="700">$ git stats --public</text>']
for i, (label, val) in enumerate(tiles):
    x, y = 30 + (i % 2) * 190, 62 + (i // 2) * 92
    o.append(f'<rect x="{x}" y="{y}" width="176" height="80" rx="10" fill="#161b22" stroke="#30363d"/>')
    o.append(f'<text x="{x+16}" y="{y+44}" fill="#58a6ff" font-size="32" font-weight="700">{val}</text>')
    o.append(f'<text x="{x+16}" y="{y+66}" fill="#8b949e" font-size="11">{label}</text>')
o.append('<text x="440" y="82" fill="#8b949e" font-size="12">TOP LANGUAGES · by bytes in public repos</text>')
bx, bw = 440, 430
x = bx
o.append(f'<clipPath id="bar"><rect x="{bx}" y="96" width="{bw}" height="14" rx="7"/></clipPath><g clip-path="url(#bar)">')
for k, v in top:
    w = bw * v / total
    o.append(f'<rect x="{x:.1f}" y="96" width="{w:.1f}" height="14" fill="{COLORS.get(k, "#8b949e")}"/>')
    x += w
o.append('</g>')
for i, (k, v) in enumerate(top):
    lx, ly = bx + (i % 2) * 220, 142 + (i // 2) * 30
    o.append(f'<circle cx="{lx+6}" cy="{ly-4}" r="5" fill="{COLORS.get(k, "#8b949e")}"/>')
    o.append(f'<text x="{lx+20}" y="{ly}" fill="#c9d1d9" font-size="13">{escape(k)}</text>')
    o.append(f'<text x="{lx+200}" y="{ly}" fill="#8b949e" font-size="13" text-anchor="end">{100*v/total:.1f}%</text>')
o.append(f'<text x="{W-30}" y="{H-14}" fill="#484f58" font-size="10" text-anchor="end">public data · auto-updated by Actions</text></svg>')
open(OUT, "w").write("\n".join(o))
print("wrote", os.path.abspath(OUT), tiles, top[:3])
