from process_steps.git_step import getDiff, getCommitLogs, formatPRUrl
from utils.env_utils import getEnv
from openai import OpenAI
import tiktoken
import os

api_key = getEnv("OPENAI_API_KEY")
base_ref = getEnv("GITHUB_BASE_REF")

def generatePRDescription():
    diff = getDiff()

    client = OpenAI(
        api_key=api_key,
    )

    mainDefaultBranches = ["main", "master"]
    description = ""

    if base_ref not in mainDefaultBranches:
        gpt_model = "gpt-4o"
        encoding = tiktoken.encoding_for_model(gpt_model)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "../templates/complete_template.txt")

        with open(template_path, "r") as file:
            template = file.read()

        prompt = f"""You are an assistant helping write professional pull request descriptions.
        Based on the code diff and the template below, generate a clear, concise, and helpful PR description: 
        Diff: {diff}
        Template: {template}
        """

        try:
            tokens = encoding.encode(prompt)
        except Exception as e:
            print(f"Failed to encode prompt: {e}")
            exit(1)

        if len(tokens) >= 30000:
            gpt_model = "gpt-4.1-mini"

        print(f"Tokens amount: {len(tokens)} & Model used: {gpt_model}")

        response = client.chat.completions.create(
            model=gpt_model,
            messages=[{"role": "user", "content": prompt}]
        )

        description = response.choices[0].message.content
    else:
        print("Generating Release PR summary...")
        commit_logs = getCommitLogs()

        pr_lines = []
        for msg in commit_logs:
            if msg.startswith("Merge pull request #"):
                parts = msg.split()
                pr_number = parts[3][1:]
                title = " ".join(parts[5:])
                pr_lines.append(formatPRUrl(pr_number, title))

        if pr_lines:
            description = "## 🚀 Release PRs:\n\n" + "\n".join(pr_lines)
        else:
            description = "No merged PRs found in this release."

    return description