import os
import subprocess
import openai

# Get the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise Exception("Missing OpenAI API Key")

# Get base branch from PR
base_ref = os.getenv("GITHUB_BASE_REF")
if not base_ref:
    raise Exception("GITHUB_BASE_REF not set")

# Mark Git directory as safe
subprocess.run(["git", "config", "--global", "--add", "safe.directory", "/github/workspace"], check=True)

# Fetch the base branch
subprocess.run(["git", "fetch", "origin", base_ref], check=True)

# Get diff and commit message
base = subprocess.check_output(["git", "merge-base", "HEAD", f"origin/{base_ref}"]).decode().strip()
diff = subprocess.check_output(["git", "diff", base, "HEAD"]).decode()
commit_msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"]).decode()

# Generate description with OpenAI
openai.api_key = api_key
prompt = f"""Generate a clear and professional PR description.

Commit message:
{commit_msg}

Code diff:
{diff}
"""

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)

description = response['choices'][0]['message']['content']
print("🔍 AI-Generated PR Description:")
print(description)

# Optional: post as comment using GitHub CLI
subprocess.run(["gh", "pr", "comment", "--body", description], check=True)
