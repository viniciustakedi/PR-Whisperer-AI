import os
import subprocess
from openai import OpenAI

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

print(response)

description = response.choices[0].message.content

print("I-Generated PR Description:\n")
print(description)
