import json
import requests
import argparse
import base64  # Import base64 for encoding the Azure token

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

def encode_azure_token(token):
    """Encodes the Azure DevOps token in Base64 format."""
    return base64.b64encode(f":{token}".encode("utf-8")).decode("utf-8")

def trigger_azure_pipeline(organization, project, pipeline_id, token, branch="main"):
    if not token:
        print("Error: Azure DevOps token is missing or invalid.")
        return

    encoded_token = encode_azure_token(token)  # Encode the token
    url = f"https://dev.azure.com/{organization}/{project}/_apis/pipelines/{pipeline_id}/runs?api-version=6.0-preview.1"
    headers = {
        "Authorization": f"Basic {encoded_token}",  # Use the encoded token
        "Content-Type": "application/json"
    }
    data = {"resources": {"repositories": {"self": {"refName": f"refs/heads/{branch}"}}}}
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"Successfully triggered Azure DevOps pipeline {pipeline_id} in {organization}/{project}")
    elif response.status_code == 401:
        print(f"Failed to trigger Azure DevOps pipeline {pipeline_id} in {organization}/{project}: Unauthorized (Bad credentials).")
    else:
        print(f"Failed to trigger Azure DevOps pipeline {pipeline_id} in {organization}/{project}: {response.status_code} - {response.text}")

def main(config_path, github_token, azure_token):
    if not github_token and not azure_token:
        print("Error: At least one token (GitHub or Azure DevOps) must be provided.")
        return

    with open(config_path, "r") as f:
        config = json.load(f)

    for item in config.get("workflows", []):
        if not item.get("enabled", True):  # Skip if the workflow is disabled
            print(f"Skipping disabled workflow for {item.get('repo', item.get('project'))}.")
            continue

        if item.get("type") == "github":
            if not github_token:
                print(f"Skipping GitHub workflow for {item['repo']} due to missing GitHub token.")
                continue
            trigger_workflow(item["repo"], item["workflow"], github_token, item.get("ref", "main"))
        elif item.get("type") == "azure":
            if not azure_token:
                print(f"Skipping Azure pipeline for {item['organization']}/{item['project']} due to missing Azure token.")
                continue
            trigger_azure_pipeline(
                item["organization"],
                item["project"],
                item["pipeline_id"],
                azure_token,
                item.get("branch", "main")
            )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CI/CD Orchestrator")
    parser.add_argument("--config", required=True, help="Path to the configuration file")
    parser.add_argument("--github-token", required=False, help="GitHub token for authentication")
    parser.add_argument("--azure-token", required=False, help="Azure DevOps token for authentication")
    args = parser.parse_args()
    main(args.config, args.github_token, args.azure_token)