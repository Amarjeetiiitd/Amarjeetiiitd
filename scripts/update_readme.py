#!/usr/bin/env python3
"""
update_readme.py
Fetches real GitHub data, generates animated SVG cards, updates README.md
"""

import os, re, requests, textwrap
from datetime import datetime, timezone
from pathlib import Path

# ── CONFIG ─────────────────────────────────────────────────────────────────
USERNAME = "Amarjeetiiitd"
TOKEN    = os.environ["GH_TOKEN"]
ROOT     = Path(__file__).resolve().parent.parent
README   = ROOT / "README.md"
SVG_DIR  = ROOT / "assets"
SVG_DIR.mkdir(exist_ok=True)

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
GQL_HEADERS = {
    "Authorization": f"bearer {TOKEN}",
    "Content-Type": "application/json",
}

# ── HELPERS ────────────────────────────────────────────────────────────────
def gh(path, params=None):
    url = f"https://api.github.com{path}"
    items, page = [], 1
    while True:
        r = requests.get(url, headers=HEADERS,
                         params={**(params or {}), "per_page": 100, "page": page})
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            if not data: break
            items.extend(data); page += 1
        else:
            return data
    return items

def graphql(query):
    r = requests.post("https://api.github.com/graphql",
                      headers=GQL_HEADERS, json={"query": query})
    r.raise_for_status()
    return r.json()["data"]

# ── FETCH DATA ─────────────────────────────────────────────────────────────
print("Fetching user info…")
user = gh(f"/users/{USERNAME}")

print("Fetching repos…")
all_repos    = gh("/user/repos", {"affiliation": "owner", "visibility": "all"})
public_repos = [r for r in all_repos if not r["private"]]
private_repos= [r for r in all_repos if r["private"]]
total_stars  = sum(r["stargazers_count"] for r in all_repos)
total_forks  = sum(r["forks_count"]      for r in all_repos)

# Languages
lang_bytes = {}
for repo in all_repos:
    try:
        langs = gh(f"/repos/{USERNAME}/{repo['name']}/languages")
        for lang, b in langs.items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + b
    except: pass

total_bytes  = sum(lang_bytes.values()) or 1
top_langs    = sorted(lang_bytes.items(), key=lambda x: -x[1])[:6]
top_langs_pct= [(l, round(b/total_bytes*100, 1)) for l, b in top_langs]

print("Fetching GraphQL stats…")
gql = graphql(f"""
{{
  user(login: "{USERNAME}") {{
    contributionsCollection {{
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {{
        totalContributions
        weeks {{ contributionDays {{ contributionCount date }} }}
      }}
    }}
    followers {{ totalCount }}
    following {{ totalCount }}
  }}
}}
""")
cc  = gql["user"]["contributionsCollection"]
cal = cc["contributionCalendar"]
total_contributions = cal["totalContributions"]
total_commits       = cc["totalCommitContributions"]
total_prs           = cc["totalPullRequestContributions"]
total_issues        = cc["totalIssueContributions"]
followers           = gql["user"]["followers"]["totalCount"]
following           = gql["user"]["following"]["totalCount"]

all_days = [d for w in cal["weeks"] for d in w["contributionDays"]]
streak = 0
for d in reversed(all_days):
    if d["contributionCount"] > 0: streak += 1
    else: break

try:
    v = gh(f"/repos/{USERNAME}/{USERNAME}/traffic/views")
    profile_views   = v.get("count", 0)
    unique_visitors = v.get("uniques", 0)
except:
    profile_views = unique_visitors = 0

now_str = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")

# ── GENERATE SVG: STATS BANNER ─────────────────────────────────────────────
LANG_COLORS = {
    "C++":"#00599C","Python":"#3776AB","JavaScript":"#F7DF1E",
    "TypeScript":"#3178C6","Jupyter Notebook":"#DA5B0B","HTML":"#E34C26",
    "CSS":"#563D7C","Java":"#B07219","Rust":"#DEA584","Go":"#00ADD8",
    "Shell":"#89E051","Other":"#6B8CAE"
}

def lang_color(name):
    return LANG_COLORS.get(name, "#6B8CAE")

def make_stats_svg(pub, priv, total, stars, forks, commits, prs, contrib, streak_d, foll, views, updated):
    stats = [
        ("📦", "Public Repos",    str(pub),    "#00E5FF"),
        ("🔒", "Private Repos",   str(priv),   "#7C4DFF"),
        ("⭐", "Total Stars",     str(stars),  "#FFEA00"),
        ("🍴", "Total Forks",     str(forks),  "#00E676"),
        ("💻", "Commits (year)",  str(commits),"#00E5FF"),
        ("🔀", "PRs (year)",      str(prs),    "#FF4081"),
        ("🏆", "Contributions",   str(contrib),"#FFEA00"),
        ("🔥", "Streak",          f"{streak_d}d","#FF6D00"),
        ("👥", "Followers",       str(foll),   "#00E676"),
        ("👁️", "Profile Views",   str(views),  "#7C4DFF"),
    ]
    cols, rows = 5, 2
    W, H = 860, 220
    cw = W // cols

    cards = ""
    for i,(icon,label,val,color) in enumerate(stats):
        col = i % cols
        row = i // cols
        x = col * cw + 10
        y = row * 88 + 16
        delay = i * 0.08
        cards += f"""
        <g transform="translate({x},{y})" opacity="0">
          <animate attributeName="opacity" from="0" to="1"
            begin="{delay:.2f}s" dur="0.5s" fill="freeze"/>
          <rect width="{cw-20}" height="76" rx="10"
            fill="#0D1B2E" stroke="{color}" stroke-width="0.8" stroke-opacity="0.4"/>
          <text x="10" y="22" font-size="18" font-family="Segoe UI Emoji,sans-serif">{icon}</text>
          <text x="{cw//2-10}" y="46" text-anchor="middle"
            font-family="'Segoe UI',sans-serif" font-size="22" font-weight="700"
            fill="{color}">{val}</text>
          <text x="{cw//2-10}" y="64" text-anchor="middle"
            font-family="'Segoe UI',sans-serif" font-size="10" fill="#6B8CAE"
            letter-spacing="0.3">{label}</text>
        </g>"""

    return f"""<svg viewBox="0 0 {W} {H+30}" xmlns="http://www.w3.org/2000/svg" width="{W}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#060B14"/>
      <stop offset="100%" stop-color="#0A1628"/>
    </linearGradient>
    <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00E5FF" stop-opacity="0.6"/>
      <stop offset="50%" stop-color="#7C4DFF" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#00E5FF" stop-opacity="0.6"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H+30}" rx="16" fill="url(#bg)"/>
  <rect width="{W}" height="{H+30}" rx="16" fill="none" stroke="url(#borderGrad)" stroke-width="1.2"/>
  {cards}
  <text x="{W//2}" y="{H+20}" text-anchor="middle"
    font-family="'Courier New',monospace" font-size="9" fill="#2A4A6A">
    ⟳ Auto-updated · {updated}
  </text>
</svg>"""

# ── GENERATE SVG: LANGUAGE BARS ────────────────────────────────────────────
def make_lang_svg(langs_pct):
    W, bh, gap, ox, oy = 860, 22, 14, 140, 20
    H = len(langs_pct) * (bh + gap) + oy + 20
    bars = ""
    for i,(lang,pct) in enumerate(langs_pct):
        y = oy + i*(bh+gap)
        bw = int((W - ox - 100) * pct / 100)
        color = lang_color(lang)
        delay = i * 0.1
        bars += f"""
        <text x="0" y="{y+16}" font-family="'Segoe UI',sans-serif"
          font-size="12" fill="#A0C4D8">{lang}</text>
        <rect x="{ox}" y="{y+4}" width="{W-ox-100}" height="{bh-8}"
          rx="4" fill="#0D1B2E"/>
        <rect x="{ox}" y="{y+4}" width="0" height="{bh-8}" rx="4" fill="{color}">
          <animate attributeName="width" from="0" to="{bw}"
            begin="{delay:.2f}s" dur="0.8s" fill="freeze"
            calcMode="spline" keySplines="0.16 1 0.3 1"/>
        </rect>
        <text x="{W-90}" y="{y+16}" font-family="'Courier New',monospace"
          font-size="11" fill="{color}">{pct}%</text>"""

    return f"""<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" width="{W}">
  <rect width="{W}" height="{H}" rx="16" fill="#060B14"/>
  <rect width="{W}" height="{H}" rx="16" fill="none"
    stroke="rgba(0,229,255,0.15)" stroke-width="1"/>
  {bars}
</svg>"""

# ── GENERATE SVG: CONTRIBUTION HEATMAP ────────────────────────────────────
def make_heatmap_svg(all_days_data):
    cs, gap = 11, 2
    cols = (len(all_days_data) + 6) // 7
    W = cols*(cs+gap)+40
    H = 7*(cs+gap)+50
    cells = ""
    for i,d in enumerate(all_days_data):
        col = i // 7
        row = i % 7
        x = col*(cs+gap)+20
        y = row*(cs+gap)+20
        c = d["contributionCount"]
        if c == 0:   color,op = "#0D1B2E",1
        elif c <= 2: color,op = "#00E5FF",0.2
        elif c <= 5: color,op = "#00E5FF",0.45
        elif c <=10: color,op = "#00E5FF",0.7
        else:        color,op = "#00E5FF",1.0
        delay = (i*0.003)
        cells += f"""<rect x="{x}" y="{y}" width="{cs}" height="{cs}" rx="2"
          fill="{color}" fill-opacity="{op}">
          <animate attributeName="fill-opacity" from="0" to="{op}"
            begin="{delay:.3f}s" dur="0.3s" fill="freeze"/>
        </rect>"""

    return f"""<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" width="{W}">
  <rect width="{W}" height="{H}" rx="12" fill="#060B14"/>
  <rect width="{W}" height="{H}" rx="12" fill="none"
    stroke="rgba(0,229,255,0.12)" stroke-width="1"/>
  {cells}
  <text x="20" y="{H-6}" font-family="'Segoe UI',sans-serif"
    font-size="9" fill="#2A4A6A">{total_contributions} contributions this year</text>
</svg>"""

# ── WRITE SVGs ─────────────────────────────────────────────────────────────
print("Generating SVG assets…")

stats_svg = make_stats_svg(
    len(public_repos), len(private_repos), len(all_repos),
    total_stars, total_forks, total_commits, total_prs,
    total_contributions, streak, followers, profile_views, now_str
)
(SVG_DIR / "stats.svg").write_text(stats_svg, encoding="utf-8")

lang_svg = make_lang_svg(top_langs_pct)
(SVG_DIR / "langs.svg").write_text(lang_svg, encoding="utf-8")

heatmap_svg = make_heatmap_svg(all_days)
(SVG_DIR / "heatmap.svg").write_text(heatmap_svg, encoding="utf-8")

# ── UPDATE README ──────────────────────────────────────────────────────────
print("Updating README.md…")

new_readme = f"""<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&height=200&section=header&text=Amarjeet%20Raj&fontSize=50&fontColor=00E5FF&animation=fadeIn&color=0:060B14,100:0A1628" width="100%"/>

<img src="https://readme-typing-svg.herokuapp.com?font=JetBrains+Mono&size=20&duration=3000&pause=1000&color=00E5FF&center=true&vCenter=true&width=700&lines=Data+Science+%26+AI+%40+IIIT+Dharwad;Machine+Learning+Engineer+in+Progress;NLP+%7C+Reinforcement+Learning+%7C+DSA;Building+Real-World+AI+Systems" />

[![Profile Views](https://komarev.com/ghpvc/?username=Amarjeetiiitd&color=00e5ff&style=flat-square&label=Profile+Views)](https://github.com/Amarjeetiiitd)
&nbsp;
[![GitHub followers](https://img.shields.io/github/followers/Amarjeetiiitd?color=00E5FF&style=flat-square&logo=github&label=Followers)](https://github.com/Amarjeetiiitd)

</div>

---

## 🚀 About Me

| | |
|---|---|
| 🎓 | Data Science & AI @ IIIT Dharwad |
| 🤖 | Exploring NLP, Reinforcement Learning & ML |
| ⚡ | Strong in DSA using C++ |
| 🎯 | Building scalable, real-world AI systems |
| 🔥 | Current Streak: **{streak} days** |

---

## 📊 Live Stats

<div align="center">

![Stats](assets/stats.svg)

</div>

---

## 🌱 Contribution Heatmap

<div align="center">

![Heatmap](assets/heatmap.svg)

</div>

---

## 🏆 GitHub Trophies

<div align="center">

[![trophy](https://github-profile-trophy.vercel.app/?username=Amarjeetiiitd&theme=darkhub&no-frame=true&no-bg=true&margin-w=6&column=7)](https://github.com/ryo-ma/github-profile-trophy)

</div>

---

## 📈 Activity Graph

<div align="center">

[![Activity Graph](https://github-readme-activity-graph.vercel.app/graph?username=Amarjeetiiitd&theme=tokyo-night&hide_border=true&area=true)](https://github.com/ashutosh00710/github-readme-activity-graph)

</div>

---

## 💻 Top Languages

<div align="center">

![Languages](assets/langs.svg)

</div>

---

## 🔥 Streak & Stats Cards

<div align="center">

<img src="https://github-readme-streak-stats.herokuapp.com/?user=Amarjeetiiitd&theme=tokyonight&hide_border=true&ring=00E5FF&fire=FFEA00&currStreakNum=00E5FF" height="165"/>
&nbsp;
<img src="https://github-readme-stats.vercel.app/api?username=Amarjeetiiitd&show_icons=true&theme=tokyonight&hide_border=true&include_all_commits=true&count_private=true&title_color=00E5FF&icon_color=7C4DFF" height="165"/>

</div>

---

## 🛠️ Tech Stack

<div align="center">

![C++](https://img.shields.io/badge/C++-00599C?style=for-the-badge&logo=cplusplus&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=node.js&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05033?style=for-the-badge&logo=git&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![VS Code](https://img.shields.io/badge/VS_Code-007ACC?style=for-the-badge&logo=visual-studio-code&logoColor=white)

</div>

---

## 🏗️ What I'm Building

<div align="center">

| 🚀 Project | 📝 Description | 🛠️ Stack |
|-----------|---------------|---------|
| ♻️ **Smart Garbage Collection** | AI-powered route optimization for waste management using RL agents | Python · RL · IoT |
| 🌱 **Decentralized Urban Farming** | ML-driven crop yield prediction & distributed resource allocation | ML · Node.js · Python |
| 🤖 **AI Career Tools** | Resume analyser + job match scoring + interview prep via NLP | NLP · BERT · FastAPI |

</div>

---

## 🔗 Connect

<div align="center">

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/amarjeet-raj)
[![Email](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:23bds006@iiitdwd.ac.in)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Amarjeetiiitd)
[![Portfolio](https://img.shields.io/badge/Portfolio-00E5FF?style=for-the-badge&logo=google-chrome&logoColor=black)](https://Amarjeetiiitd.github.io/Amarjeetiiitd/portfolio.html)

</div>

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0A1628,100:00E5FF&height=100&section=footer" width="100%"/>

*🤖 README & SVG stats auto-updated every 6 hours via [GitHub Actions](https://github.com/Amarjeetiiitd/Amarjeetiiitd/actions) · Last sync: {now_str}*

</div>
"""

README.write_text(new_readme, encoding="utf-8")
print(f"✅ Done! Public:{len(public_repos)} Private:{len(private_repos)} Stars:{total_stars} Streak:{streak}d")
