import json
import requests
import argparse

def trigger_workflow(repo, workflow, token, ref="main"):
    if not token:
        print("Error: GitHub token is missing or invalid.")
        return

    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"ref": ref}
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 204:
        print(f"Successfully triggered workflow {workflow} in {repo}")
    elif response.status_code == 401:
        print(f"Failed to trigger workflow {workflow} in {repo}: Unauthorized (Bad credentials).")
    else:
        print(f"Failed to trigger workflow {workflow} in {repo}: {response.status_code} - {response.text}")

def main(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)

    token = config.get("github_token")
    if not token:
        print("Error: 'github_token' is missing in the configuration file.")
        return

    for item in config.get("workflows", []):
        trigger_workflow(item["repo"], item["workflow"], token, item.get("ref", "main"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Actions Orchestrator")
    parser.add_argument("--config", required=True, help="Path to the configuration file")
    args = parser.parse_args()
    main(args.config)