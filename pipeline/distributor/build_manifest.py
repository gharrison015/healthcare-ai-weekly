import json
import os
import glob

def build_manifest(repo_dir="/Users/greg/Claude/healthcare-ai-weekly"):
    issues = []
    pattern = os.path.join(repo_dir, "issues", "*", "data.json")
    for data_file in sorted(glob.glob(pattern)):
        date = os.path.basename(os.path.dirname(data_file))
        with open(data_file) as f:
            data = json.load(f)
        issues.append({
            "date": date,
            "week_range": data.get("week_range", ""),
            "editorial_summary": data.get("editorial_summary", ""),
            "top_stories": len(data.get("sections", {}).get("top_stories", [])),
            "vbc_watch": len(data.get("sections", {}).get("vbc_watch", [])),
            "ma_partnerships": len(data.get("sections", {}).get("ma_partnerships", [])),
            "consulting_intelligence": len(data.get("sections", {}).get("consulting_intelligence", [])),
            "did_you_know": len(data.get("sections", {}).get("did_you_know", [])),
        })

    manifest_path = os.path.join(repo_dir, "issues.json")
    with open(manifest_path, "w") as f:
        json.dump(issues, f, indent=2)

    print(f"Manifest updated: {len(issues)} issues")
    return issues

if __name__ == "__main__":
    build_manifest()
