#!/usr/bin/env python3
"""
update_readme.py
Fetches real data from GitHub API and rewrites README.md stats sections.
Run via GitHub Actions with a PAT that has: repo, read:user scopes.
"""

import os, re, requests
from datetime import datetime, timezone
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
USERNAME   = "Amarjeetiiitd"
TOKEN      = os.environ["GH_TOKEN"]
README     = Path(__file__).resolve().parent.parent / "README.md"
HEADERS    = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
GQL_HEADERS = {
    "Authorization": f"bearer {TOKEN}",
    "Content-Type": "application/json",
}

# ── HELPERS ───────────────────────────────────────────────────────────────────
def gh(path, params=None):
    """REST API call (paginated if needed)."""
    url = f"https://api.github.com{path}"
    items, page = [], 1
    while True:
        r = requests.get(url, headers=HEADERS,
                         params={**(params or {}), "per_page": 100, "page": page})
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            if not data:
                break
            items.extend(data)
            page += 1
        else:
            return data        # single-object endpoints
    return items

def graphql(query):
    r = requests.post("https://api.github.com/graphql",
                      headers=GQL_HEADERS, json={"query": query})
    r.raise_for_status()
    return r.json()["data"]

# ── FETCH DATA ─────────────────────────────────────────────────────────────────
print("Fetching user info…")
user = gh(f"/users/{USERNAME}")

# All repos (public + private) — /user/repos includes private when authenticated
print("Fetching repos…")
all_repos = gh("/user/repos", {"affiliation": "owner", "visibility": "all"})

public_repos  = [r for r in all_repos if not r["private"]]
private_repos = [r for r in all_repos if r["private"]]
total_stars   = sum(r["stargazers_count"] for r in all_repos)
total_forks   = sum(r["forks_count"]      for r in all_repos)

# Languages
lang_bytes = {}
for repo in all_repos:
    try:
        langs = gh(f"/repos/{USERNAME}/{repo['name']}/languages")
        for lang, b in langs.items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + b
    except Exception:
        pass

total_bytes = sum(lang_bytes.values()) or 1
top_langs = sorted(lang_bytes.items(), key=lambda x: -x[1])[:6]
top_langs_pct = [(l, round(b / total_bytes * 100, 1)) for l, b in top_langs]

# Contribution stats via GraphQL (includes private)
print("Fetching contribution stats via GraphQL…")
gql_data = graphql(f"""
{{
  user(login: "{USERNAME}") {{
    contributionsCollection {{
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalRepositoriesWithContributedCommits
      contributionCalendar {{
        totalContributions
        weeks {{
          contributionDays {{
            contributionCount
          }}
        }}
      }}
    }}
    followers {{ totalCount }}
    following {{ totalCount }}
  }}
}}
""")

cc   = gql_data["user"]["contributionsCollection"]
cal  = cc["contributionCalendar"]

total_contributions = cal["totalContributions"]
total_commits       = cc["totalCommitContributions"]
total_prs           = cc["totalPullRequestContributions"]
total_issues        = cc["totalIssueContributions"]
followers           = gql_data["user"]["followers"]["totalCount"]
following           = gql_data["user"]["following"]["totalCount"]

# Current streak
all_days = [
    d["contributionCount"]
    for week in cal["weeks"]
    for d in week["contributionDays"]
]
streak = 0
for count in reversed(all_days):
    if count > 0:
        streak += 1
    else:
        break

# Profile views (requires traffic API — works on your OWN repos)
# We fetch traffic for the special username/username repo
try:
    views_data = gh(f"/repos/{USERNAME}/{USERNAME}/traffic/views")
    profile_views = views_data.get("count", "N/A")
    unique_visitors = views_data.get("uniques", "N/A")
except Exception:
    profile_views = "N/A"
    unique_visitors = "N/A"

# ── BUILD README SECTION ───────────────────────────────────────────────────────
now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

stats_md = f"""
| 📦 Stat | 🔢 Count |
|---------|---------|
| Public Repos | **{len(public_repos)}** |
| Private Repos | **{len(private_repos)}** |
| Total Repos | **{len(all_repos)}** |
| ⭐ Total Stars | **{total_stars}** |
| 🍴 Total Forks | **{total_forks}** |
| 🔀 Total PRs (this year) | **{total_prs}** |
| 🐛 Issues Opened (this year) | **{total_issues}** |
| 🏆 Contributions (this year) | **{total_contributions}** |
| 💻 Commits (this year) | **{total_commits}** |
| 🔥 Current Streak | **{streak} days** |
| 👥 Followers | **{followers}** |
| 👣 Following | **{following}** |
| 👁️ Profile Views (14d) | **{profile_views}** |
| 🌐 Unique Visitors (14d) | **{unique_visitors}** |

**Top Languages (by bytes across all repos):**

| Language | % |
|----------|---|
""" + "\n".join(f"| {l} | {p}% |" for l, p in top_langs_pct) + f"""

*Last updated: {now}*
"""

# ── WRITE BACK ────────────────────────────────────────────────────────────────
with open(README, "r", encoding="utf-8") as f:
    content = f.read()

def replace_section(text, start_tag, end_tag, replacement):
    pattern = rf"({re.escape(start_tag)}).*?({re.escape(end_tag)})"
    return re.sub(pattern, rf"\1\n{replacement}\n\2", text, flags=re.DOTALL)

content = replace_section(
    content,
    "<!-- DYNAMIC_STATS_START -->",
    "<!-- DYNAMIC_STATS_END -->",
    stats_md.strip()
)

with open(README, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ README updated successfully!")
print(f"   Public: {len(public_repos)}  Private: {len(private_repos)}  Stars: {total_stars}  Streak: {streak}d")
