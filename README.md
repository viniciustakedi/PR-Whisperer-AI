# 🤖 PR Whisperer AI

AI-powered GitHub Action that automatically generates clear, professional Pull Request descriptions based on your code diff — powered by OpenAI's GPT-4.

---

## ✨ Features

- 🔍 Analyzes `git diff` between the PR branch and base
- 🧠 Summarizes changes using OpenAI GPT-4o for PRs with until 30k tokens and gpt-4.1-mini for PRs with until 200k tokens
- 💬 (Optional) Posts generated description as a PR comment
- 🛠️ Easy to drop into any CI/CD workflow

---

## 🚀 Usage

### 1. Create or update your workflow

Add this to your `.github/workflows/pr-whisperer.yml`:

```yaml
name: PR Whisperer AI

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  whisper:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run PR Whisperer AI
        uses: viniciustakedi/PR-Whisperer-AI@main
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Add your secret 🔐

In your repository:

- Go to Settings → Secrets → Actions
- Click New repository secret
- Name: OPENAI_API_KEY
- Value: your actual OpenAI API key

### 🔧 How It Works

1. Fetches the base branch and current HEAD
2. Computes the diff using git merge-base and git diff
3. Sends the diff to OpenAI's API with a prompt
4. Prints the AI-generated PR description in the logs
(Coming soon) Optionally posts it to the PR body or comments

### 📦 Development

Install locally (optional)

```bash
pip install -r requirements.txt
python main.py
```
