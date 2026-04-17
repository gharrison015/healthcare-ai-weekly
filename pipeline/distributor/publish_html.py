import os
import json
import shutil
import subprocess

def build_issue_path(date_str):
    return f"issues/{date_str}"

def publish_to_repo(html_content, curated_data, date_str,
                    repo_dir="/Users/greg/Claude/personal/content/healthcare-ai-weekly",
                    local_backup_dir="data/issues"):
    issue_path = build_issue_path(date_str)

    local_dir = os.path.join(local_backup_dir, date_str)
    os.makedirs(local_dir, exist_ok=True)
    with open(os.path.join(local_dir, "index.html"), "w") as f:
        f.write(html_content)
    with open(os.path.join(local_dir, "data.json"), "w") as f:
        json.dump(curated_data, f, indent=2)

    if os.path.exists(repo_dir):
        repo_issue_dir = os.path.join(repo_dir, issue_path)
        os.makedirs(repo_issue_dir, exist_ok=True)
        shutil.copy2(os.path.join(local_dir, "index.html"), repo_issue_dir)
        shutil.copy2(os.path.join(local_dir, "data.json"), repo_issue_dir)

        subprocess.run(["git", "add", issue_path], cwd=repo_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Add issue {date_str}"],
            cwd=repo_dir, capture_output=True,
        )
        subprocess.run(["git", "push"], cwd=repo_dir, capture_output=True)
        print(f"Published to repo: {issue_path}")
    else:
        print(f"Repo not found at {repo_dir}, saved locally only: {local_dir}")

    return local_dir
