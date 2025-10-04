# Video Fact Checker

Automatically fact-check YouTube videos using AI and display results as interactive overlays.

## 🚀 How It Works

1. User pastes a YouTube URL
2. Browser triggers a GitHub Actions workflow
3. Workflow fetches transcript and fact-checks using OpenAI
4. Results are saved to the repo
5. Browser displays fact-checks as timed overlays on the video

## 📋 Setup Instructions

### 1. Clone/Setup Repository

This repo should already be set up at: `https://github.com/factcheck47/video-fact-checker`

### 2. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy it (you'll need it next)

### 3. Add Secrets to GitHub

1. Go to your repo: Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add secret:
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key

### 4. Create Personal Access Token (PAT)

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a name like "Fact Checker App"
4. Select scopes:
   - ✅ `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you can't see it again!)

### 5. Add PAT to Frontend

1. Open `js/github-api.js`
2. Find line: `token: 'YOUR_GITHUB_PAT_HERE'`
3. Replace with your actual token: `token: 'ghp_xxxxxxxxxxxx'`

⚠️ **Security Note**: Your PAT will be visible in the public repo. Use fine-grained tokens with minimal permissions for better security. For a truly secure version, you'd need a separate backend server.

### 6. Enable GitHub Pages

1. Go to repo Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` / `root`
4. Save

Your site will be live at: `https://factcheck47.github.io/video-fact-checker/`

### 7. Create Empty Results Folder

Create a `.gitkeep` file in the `results/` folder:
```bash
mkdir -p results
touch results/.gitkeep
git add results/.gitkeep
git commit -m "Add results folder"
git push
```

## 🧪 Testing

1. Go to your GitHub Pages site
2. Paste a YouTube URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
3. Click "Check Facts"
4. Wait 1-2 minutes for processing
5. Watch the fact-checks appear!

## 📁 File Structure

```
├── .github/workflows/
│   └── fact-check.yml          # Workflow definition
├── scripts/
│   └── fact_check.py           # Processing logic
├── results/                     # Generated fact-checks
├── css/
│   └── style.css               # Styling
├── js/
│   ├── app.js                  # Main app logic
│   ├── github-api.js           # GitHub API client
│   └── video-player.js         # Video player + overlays
├── index.html                   # Main page
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔧 Troubleshooting

**Workflow not triggering?**
- Check PAT has `repo` scope
- Verify PAT is correctly added to `github-api.js`

**No results after 2 minutes?**
- Check Actions tab in GitHub to see workflow runs
- Look for error messages in workflow logs

**OpenAI errors?**
- Verify API key is correct in repository secrets
- Check you have API credits

## 💡 Future Improvements

- Add more AI providers (Claude, Gemini)
- Better timestamp matching
- Support for other video platforms
- Caching improvements
- User authentication
- Rate limiting

## 📝 License

MIT - Feel free to use and modify!
