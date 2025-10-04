# Video Fact Checker

Automatically fact-check YouTube videos using AI and display results as interactive overlays.

## 🚀 How It Works

1. User pastes a YouTube URL into the app
2. App checks for cached results
3. If not cached, user creates a GitHub issue (one click, pre-filled)
4. Scheduled workflow runs every 5 minutes and processes all pending issues
5. Results are saved to the repo and displayed with timed overlays

## 🔒 Security & Privacy

- ✅ **No API tokens in browser code** - completely secure
- ✅ **Anonymous GitHub account** - maintains privacy
- ✅ **API keys safe in GitHub Secrets** - never exposed
- ✅ **Public repo, private credentials** - best of both worlds

## 📋 Setup Instructions

### 1. Repository Setup

Your repo: `https://github.com/factcheck47/video-fact-checker`

### 2. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy it

### 3. Add OpenAI Key to GitHub Secrets

1. Go to repo: **Settings → Secrets and variables → Actions**
2. Click **"New repository secret"**
3. Add secret:
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key from step 2

### 4. Enable GitHub Pages

1. Go to repo: **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: **`main`** / **`root`**
4. Click **Save**

Your site will be live at: `https://factcheck47.github.io/video-fact-checker/`

### 5. Create Results Folder

```bash
mkdir -p results
touch results/.gitkeep
git add results/.gitkeep
git commit -m "Add results folder"
git push
```

### 6. Enable GitHub Actions

1. Go to repo: **Actions** tab
2. If prompted, click **"I understand my workflows, go ahead and enable them"**

The scheduled workflow will now run every 5 minutes automatically!

## 🎯 How to Use

1. Go to your GitHub Pages site: `https://factcheck47.github.io/video-fact-checker/`
2. Paste a YouTube URL
3. Click **"Check Facts"**
4. If not cached:
   - Click the link to create a GitHub issue (opens in new tab)
   - Submit the pre-filled issue
   - Return to the app and wait (~5 minutes max)
5. Watch fact-checks appear as overlays!

## 📁 File Structure

```
├── .github/workflows/
│   └── fact-check.yml          # Scheduled workflow (every 5 min)
├── scripts/
│   ├── fact_check.py           # Original script (kept for reference)
│   └── process_queue.py        # Queue processor (checks issues)
├── results/                     # Generated fact-checks
│   └── {video_id}.json
├── css/
│   └── style.css
├── js/
│   ├── app.js                  # Main app logic
│   ├── github-api.js           # GitHub API (NO TOKENS!)
│   └── video-player.js         # Video player + overlays
├── index.html
├── requirements.txt
└── README.md
```

## 🔧 How The Queue System Works

1. **User creates issue** with title: `Fact-check: VIDEO_ID`
2. **Scheduled workflow** (runs every 5 min) scans for open issues
3. **For each issue:**
   - Extract video ID from title
   - Fetch YouTube transcript
   - Fact-check with OpenAI
   - Save results to `results/{video_id}.json`
   - Close issue with success/failure comment
4. **Browser polls** for results file (no auth needed - public repo)
5. **Display** results with overlays

## 🧪 Testing

1. Go to your GitHub Pages site
2. Paste: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
3. Click "Check Facts"
4. Click the issue link and submit
5. Wait up to 5 minutes
6. Watch the magic happen! ✨

## 🔧 Troubleshooting

**Issue not being processed?**
- Check **Actions** tab to see workflow runs
- Workflow runs every 5 minutes on the schedule
- Check issue was created with correct title format: `Fact-check: VIDEO_ID`

**Workflow not running?**
- Ensure Actions are enabled (Settings → Actions)
- Check workflow file exists at `.github/workflows/fact-check.yml`

**OpenAI errors in workflow logs?**
- Verify API key is correct in Secrets
- Check you have API credits available

**Results not appearing?**
- Wait full 5 minutes for next workflow run
- Check workflow completed successfully in Actions tab
- Verify results file was created in `results/` folder

## ⚡ Performance Notes

- **Workflow frequency:** Every 5 minutes (GitHub Actions limit)
- **Processing time:** ~30-60 seconds per video
- **Queue capacity:** Unlimited (all open issues are processed)
- **Caching:** Once processed, results are cached forever

## 💡 Future Improvements

- Webhook-based triggering (requires external server)
- Support for other video platforms
- Multiple AI provider options
- Better timestamp matching algorithms
- Video chapters integration
- Export functionality

## 📝 License

MIT - Feel free to use and modify!

---

**No tokens in browser code. No security vulnerabilities. Fully anonymous. 🔒**
