import os
import subprocess
from openai import OpenAI
import json
import requests
import tiktoken

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise Exception("Missing OpenAI API key")

base_ref = os.getenv("GITHUB_BASE_REF")
if not base_ref:
    raise Exception("GITHUB_BASE_REF is not set")

subprocess.run(["git", "config", "--global", "--add", "safe.directory", "/github/workspace"], check=True)
subprocess.run(["git", "fetch", "--all"], check=True)

branches = subprocess.check_output(["git", "branch", "-r"]).decode()
print("Remote branches:\n", branches)

try:
    base = subprocess.check_output(["git", "merge-base", "HEAD", f"origin/{base_ref}"]).decode().strip()
except subprocess.CalledProcessError:
    print(f"merge-base failed between HEAD and origin/{base_ref}. Falling back to origin/{base_ref}")
    base = f"origin/{base_ref}"

try:
    diff = subprocess.check_output(["git", "diff", base, "HEAD"]).decode()
except subprocess.CalledProcessError as e:
    print(f"Failed to get git diff:\n{e}")
    exit(1)

if not diff.strip():
    print("No changes found in diff. Exiting.")
    exit(0)

client = OpenAI(
    api_key=api_key,
)

mainDefaultBranches = ["main", "master"]
description = ""

if base_ref not in mainDefaultBranches:
    gpt_model = "gpt-4o"
    encoding = tiktoken.encoding_for_model(gpt_model)

    prompt = f"""You are an assistant helping write professional pull request descriptions.

    Based on the code diff below, generate a clear, concise, and helpful PR description with this template: # 🚀 PR Title

**Short description of the change (max 1–2 lines).**

---

## 📖 Description

- **What’s changing?**  
  A concise overview of the changes you’ve made.

- **Why?**  
  The motivation behind this PR (bug-fix, feature, refactor, docs, etc.).

---

## 🛠 Implementation Details

- Bullet out the key technical changes:
  - e.g. “Extracted `FooService` from `BarController` for better separation of concerns”
  - e.g. “Added validation on incoming payloads to prevent X error”
  - e.g. “Upgraded dependencies: `libX` v1.2.0 → v1.3.0”

---

## ✅ Checklist

- [ ] My code follows the project’s style guides  
- [ ] I added/updated tests for new behavior  
- [ ] All existing tests pass (`npm test` / `go test` / etc.)  
- [ ] I updated relevant documentation (README, OpenAPI spec, etc.)  
- [ ] I ran linting and formatting (e.g. `eslint`, `gofmt`, `prettier`)  

---

## 🔗 Related Issues / Tickets

- Closes #123  
- Fixes JIRA-456  

---
diff:
    {diff}
    """

    try:
        tokens = encoding.encode(prompt)
    except Exception as e:
        print(f"Failed to encode prompt: {e}")
        exit(1)

    if len(tokens) >= 30000:
        gpt_model = "gpt-4.1-mini"

    response = client.chat.completions.create(
        model=gpt_model,
        messages=[{"role": "user", "content": prompt}]
    )

    description = response.choices[0].message.content
else:
    print("Generating Release PR summary...")
    commit_logs = subprocess.check_output(["git", "log", "--pretty=format:%s", f"{base}..HEAD"]).decode().split("\n")

    pr_lines = []
    for msg in commit_logs:
        if msg.startswith("Merge pull request #"):
            parts = msg.split()
            pr_number = parts[3][1:]
            title = " ".join(parts[5:])
            pr_lines.append(f"- [#{pr_number}](https://github.com/{repo}/pull/{pr_number}): {title}")

    if pr_lines:
        description = "## 🚀 Release PRs:\n\n" + "\n".join(pr_lines)
    else:
        description = "No merged PRs found in this release."

event_path = os.getenv("GITHUB_EVENT_PATH")
with open(event_path, "r") as f:
    event = json.load(f)

pr_number = event["number"]
repo = os.getenv("GITHUB_REPOSITORY")
token = os.getenv("GITHUB_TOKEN")

url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}

data = {"body": description}

res = requests.patch(url, headers=headers, json=data)

if res.status_code == 200:
    print("PR description updated successfully.")
else:
    print("Failed to update PR description.")
    print(res.status_code, res.text)