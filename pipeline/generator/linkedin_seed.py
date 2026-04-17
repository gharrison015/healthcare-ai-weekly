import json
import os

def generate_seed(curated):
    linkedin = curated.get("linkedin_seed", {})
    return {
        "issue_date": curated.get("issue_date", ""),
        "top_story": linkedin.get("top_story"),
        "hook": linkedin.get("hook"),
        "angle": linkedin.get("angle"),
        "source": "healthcare-ai-weekly",
    }

def save_seed(seed, output_dir="data/linkedin-seed"):
    os.makedirs(output_dir, exist_ok=True)
    date = seed.get("issue_date", "unknown")
    path = os.path.join(output_dir, f"{date}.json")
    with open(path, "w") as f:
        json.dump(seed, f, indent=2)
    return path

def copy_to_linkedin_agent(seed, agent_dir="/Users/greg/Claude/personal/content/linkedin-agent"):
    inbox = os.path.join(agent_dir, "newsletter-seeds")
    os.makedirs(inbox, exist_ok=True)
    date = seed.get("issue_date", "unknown")
    path = os.path.join(inbox, f"{date}.json")
    with open(path, "w") as f:
        json.dump(seed, f, indent=2)
    return path
