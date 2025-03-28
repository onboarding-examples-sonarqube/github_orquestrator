import json
import requests
import argparse

def trigger_workflow(repo, workflow, token, ref="main"):
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"ref": ref}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 204:
        print(f"Successfully triggered workflow {workflow} in {repo}")
    else:
        print(f"Failed to trigger workflow {workflow} in {repo}: {response.text}")

def main(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)

    token = config["github_token"]
    for item in config["workflows"]:
        trigger_workflow(item["repo"], item["workflow"], token, item.get("ref", "main"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Actions Orchestrator")
    parser.add_argument("--config", required=True, help="Path to the configuration file")
    args = parser.parse_args()
    main(args.config)