from utils.env_utils import getEnv
import subprocess
import requests
import json

base_ref = getEnv("GITHUB_BASE_REF")
token = getEnv("GITHUB_TOKEN")
repo = getEnv("GITHUB_REPOSITORY")
event_path = getEnv("GITHUB_EVENT_PATH")

def getDiff():
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
    
    return diff

def updatePRDescription(description):
    with open(event_path, "r") as f:
        event = json.load(f)

    pr_number = event["number"]

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
    
    return

def getCommitLogs():
    try:
        base = subprocess.check_output(
            ["git", "merge-base", "HEAD", f"origin/{base_ref}"]
        ).decode().strip()
    except subprocess.CalledProcessError:
        base = f"origin/{base_ref}"

    lines = subprocess.check_output(
        ["git", "log", "--pretty=format:%s", f"{base}..HEAD"]
    ).decode().split("\n")

    return lines

def formatPRUrl(pr_number, title):
    return f"- [#{pr_number}](https://github.com/{repo}/pull/{pr_number}): {title}"