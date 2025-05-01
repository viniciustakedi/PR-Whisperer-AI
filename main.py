import os
import subprocess
from openai import OpenAI
import json
import requests

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

prompt = f"""You are an assistant helping write professional pull request descriptions.

Based on the code diff below, generate a clear, concise, and helpful PR description:

{diff}
"""

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}]
)

description = response.choices[0].message.content

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