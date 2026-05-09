# 📖 Complete Setup Guide — Amarjeet's Auto-Profile System

## What this does
- Fetches **real** data from GitHub API every 6 hours
- Automatically commits updated stats to your README
- Shows: public repos, private repos, total stars, forks, PRs,
  issues, commits, streak, followers, profile views, top languages

---

## Step 1 — Create the special profile repo (if not done)

1. Go to **github.com/new**
2. Name the repo exactly: `Amarjeetiiitd` (same as your username)
3. Make it **Public**
4. Check "Add a README file"
5. Click Create repository

---

## Step 2 — Generate a Personal Access Token (PAT)

1. Go to → **github.com/settings/tokens**
2. Click **"Generate new token (classic)"**
3. Give it a name: `profile-readme-bot`
4. Set expiration: **No expiration** (or 1 year)
5. Check these scopes:
   - ✅ `repo` (full repo access — needed for private repo count)
   - ✅ `read:user`
   - ✅ `user:email`
6. Click **Generate token**
7. **Copy it now** — you won't see it again!

---

## Step 3 — Add the token as a Secret

1. Go to your profile repo: `github.com/Amarjeetiiitd/Amarjeetiiitd`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `GH_TOKEN`
5. Value: paste your token from Step 2
6. Click **Add secret**

---

## Step 4 — Add the files to your repo

Upload/create these files in your `Amarjeetiiitd` repo:

```
Amarjeetiiitd/
├── README.md                              ← from this package
├── scripts/
│   └── update_readme.py                  ← from this package
└── .github/
    └── workflows/
        └── update-readme.yml             ← from this package
```

You can do this via:
- GitHub web UI (drag and drop files)
- Or `git clone`, copy files, then `git push`

---

## Step 5 — Run it manually first

1. Go to your repo → **Actions** tab
2. Click **"Update README Stats"** on the left
3. Click **"Run workflow"** → **"Run workflow"**
4. Watch it run — takes ~1 minute
5. After it finishes, check your README — stats will be live!

---

## What each stat needs

| Stat | API used | Notes |
|------|----------|-------|
| Public repo count | REST `/user/repos` | Automatic |
| Private repo count | REST `/user/repos` | Needs `repo` scope in PAT |
| Total stars/forks | REST `/user/repos` | Automatic |
| Contributions/commits/PRs | GraphQL | Includes private activity |
| Current streak | GraphQL calendar | Calculated from contribution calendar |
| Followers/following | GraphQL | Automatic |
| Profile views | REST traffic API | Only works on your own repo |
| Top languages | REST `/repos/{name}/languages` | Scans ALL your repos |

---

## Profile Views Counter (komarev badge)

The line below in your README shows a live profile view counter —
no setup needed, it works automatically:

```markdown
![Profile Views](https://komarev.com/ghpvc/?username=Amarjeetiiitd&color=00e5ff&style=flat-square&label=Profile+Views)
```

---

## Adding more services (optional)

Add these `<img>` tags to your README for extra automated visuals:

```markdown
<!-- GitHub Stats Card (includes private commits if token used) -->
![Stats](https://github-readme-stats.vercel.app/api?username=Amarjeetiiitd&show_icons=true&count_private=true&theme=tokyonight)

<!-- Streak -->
![Streak](https://github-readme-streak-stats.herokuapp.com/?user=Amarjeetiiitd&theme=tokyonight)

<!-- Top Languages -->
![Langs](https://github-readme-stats.vercel.app/api/top-langs/?username=Amarjeetiiitd&layout=compact&theme=tokyonight)

<!-- Activity Graph -->
![Activity](https://github-readme-activity-graph.vercel.app/graph?username=Amarjeetiiitd&theme=tokyo-night)

<!-- WakaTime (optional — needs WakaTime account + separate action) -->
![Waka](https://github-readme-stats.vercel.app/api/wakatime?username=your_wakatime_username&theme=tokyonight)
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Action fails with 401 | Token expired or wrong scopes — regenerate |
| Private repos show 0 | PAT missing `repo` scope |
| Profile views show N/A | Normal on first run, works after views accumulate |
| No changes committed | Stats didn't change — that's fine |
| Languages show wrong % | Some repos may be forks — edit script to skip forks |

---

## Schedule

The workflow runs:
- Every **6 hours** automatically (cron: `0 */6 * * *`)
- On every **push** to main (excluding README.md pushes)
- Manually any time from the **Actions** tab

To change frequency, edit the `cron` line in `update-readme.yml`.
Example: `0 0 * * *` = once daily at midnight UTC.
