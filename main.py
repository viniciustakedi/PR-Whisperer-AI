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

# response = client.chat.completions.create(
#     model="gpt-4o",
#     messages=[{"role": "user", "content": prompt}]
# )

# description = response.choices[0].message.content

description = f"""
## Pull Request Description
### Summary
This pull request introduces several enhancements and new features to the project. These changes include the integration of a GitHub Actions workflow, significant enhancements to internationalization (i18n) configurations, improvements in the styling and assets of the portfolio project, and the addition of a URL shortener feature.
### Key Changes
1. **GitHub Actions:**
   - Added a new GitHub Actions workflow file (`pr-whisperer-ai.yml`) to generate pull request descriptions using PR Whisperer AI, triggered on pull request events like opened, synchronized, and edited.
2. **Internationalization Enhancements:**
   - Added error handling to the language configurations for English (`en.ts`) and Portuguese (`pt.ts`), which will display user-friendly error messages when loading job experiences fails.
   - Refactored content configurations to use HTML strings for text segments, enabling rich text rendering.
3. **Asset and Styling Updates:**
   - Updated styles and images to enhance the visual presentation, including new class variants and oklch-based color configurations.
   - Improved 'About' section layouts and added responsive and accessible design elements.
   - Transitioned profile photo format from JPEG to WEBP for better performance.
4. **New UI Components:**
   - Introduced new UI components such as Button, Card, Input, and Progress components with a consistent design pattern using Radix UI and TailwindCSS.
5. **URL Shortening Feature:**
   - Implemented a feature to create and manage short URLs:
     - The `UrlShortener` component allows users to generate short URLs from long URLs.
     - The `RedirectPage` component facilitates redirection from short URLs to the original URLs.
   - Added APIs in the `requests/get` and `requests/post` directories to handle backend communication for URL shortening.
6. **Dependency Updates:**
   - Updated `package.json` and `package-lock.json` with new dependencies including, but not limited to, `@radix-ui/react-progress`, `class-variance-authority`, and `tailwind-merge` to support new features and styling.
### Additional Changes
- Updated `.gitignore` to exclude `.vscode` related files from version control.
- Modified ESLint and Tailwind configurations to accommodate new development patterns.
- Enhanced error feedback mechanisms across components.
### Testing
- Run the workflow to verify GitHub Actions for PR description generation.
- Verify the i18n changes by switching between supported languages and observing error messages for loading job experiences.
- Test the URL shortening functionality to ensure URLs are generated and redirected correctly.
- Validate the styling improvements in various screen sizes for responsiveness and accessibility.
This pull request targets improving user experience across multiple facets of the application while introducing critical new functionalities like URL shortening and automated PR description generation.
"""

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