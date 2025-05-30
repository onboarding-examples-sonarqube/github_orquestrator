import json
import requests
import argparse
import base64  # Import base64 for encoding the Azure token
import time    # Import time for sleep functionality
import sys     # Import sys for exit functionality

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
        run_id = response.json().get("id")
        return run_id
    elif response.status_code == 401:
        print(f"Failed to trigger Azure DevOps pipeline {pipeline_id} in {organization}/{project}: Unauthorized (Bad credentials).")
        return None
    else:
        print(f"Failed to trigger Azure DevOps pipeline {pipeline_id} in {organization}/{project}: {response.status_code} - {response.text}")
        return None

def get_workflow_run_id(repo, workflow, token):
    """Get the latest run ID for a specific workflow."""
    if not token:
        print("Error: GitHub token is missing or invalid.")
        return None

    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/runs"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"per_page": 1, "branch": "main"}  # Get the latest run

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        runs = response.json().get("workflow_runs", [])
        if runs:
            return runs[0]["id"]
    
    return None

def wait_for_github_workflow(repo, workflow, run_id, token, timeout=3600, check_interval=30):
    """Wait for a GitHub workflow run to complete."""
    if not run_id or not token:
        return False
        
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            run_data = response.json()
            status = run_data.get("status")
            conclusion = run_data.get("conclusion")
            
            print(f"GitHub workflow {workflow} in {repo} status: {status}")
            
            if status == "completed":
                if conclusion == "success":
                    print(f"GitHub workflow {workflow} in {repo} completed successfully.")
                    return True
                else:
                    print(f"GitHub workflow {workflow} in {repo} completed with conclusion: {conclusion}")
                    return False
        
        time.sleep(check_interval)
    
    print(f"Timeout waiting for GitHub workflow {workflow} in {repo} to complete.")
    return False

def wait_for_azure_pipeline(organization, project, run_id, token, timeout=3600, check_interval=30):
    """Wait for an Azure DevOps pipeline run to complete."""
    if not run_id or not token:
        return False
        
    encoded_token = encode_azure_token(token)
    url = f"https://dev.azure.com/{organization}/{project}/_apis/pipelines/runs/{run_id}?api-version=6.0-preview.1"
    headers = {
        "Authorization": f"Basic {encoded_token}",
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            run_data = response.json()
            state = run_data.get("state")
            result = run_data.get("result")
            
            print(f"Azure DevOps pipeline run {run_id} in {organization}/{project} state: {state}")
            
            if state == "completed":
                if result == "succeeded":
                    print(f"Azure DevOps pipeline run {run_id} in {organization}/{project} completed successfully.")
                    return True
                else:
                    print(f"Azure DevOps pipeline run {run_id} in {organization}/{project} completed with result: {result}")
                    return False
        
        time.sleep(check_interval)
    
    print(f"Timeout waiting for Azure DevOps pipeline run {run_id} in {organization}/{project} to complete.")
    return False

def main(config_path, github_token, azure_token, wait_for_completion=True, timeout=3600, check_interval=30, continue_on_error=False):
    """
    Main function to orchestrate pipeline/workflow runs.
    
    Args:
        config_path (str): Path to the config file
        github_token (str): GitHub token for authentication
        azure_token (str): Azure DevOps token for authentication
        wait_for_completion (bool): Whether to wait for each pipeline to complete before starting the next one
        timeout (int): Maximum time to wait for a pipeline to complete (in seconds)
        check_interval (int): Time between status checks (in seconds)
        continue_on_error (bool): Whether to continue with the next pipeline if the current one fails
    """
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
                
            # Trigger the GitHub workflow
            trigger_workflow(item["repo"], item["workflow"], github_token, item.get("ref", "main"))
            
            # Wait for the workflow to complete if requested
            if wait_for_completion:
                print(f"Waiting for GitHub workflow {item['workflow']} in {item['repo']} to complete...")
                # Wait a moment to let the API register the new run
                time.sleep(5)
                run_id = get_workflow_run_id(item["repo"], item["workflow"], github_token)
                if run_id:
                    success = wait_for_github_workflow(
                        item["repo"], 
                        item["workflow"], 
                        run_id, 
                        github_token, 
                        timeout, 
                        check_interval
                    )
                    if not success and not continue_on_error:
                        print("Stopping execution due to workflow failure.")
                        return
                else:
                    print(f"Could not get run ID for workflow {item['workflow']} in {item['repo']}.")
                    if not continue_on_error:
                        print("Stopping execution.")
                        return
                        
        elif item.get("type") == "azure":
            if not azure_token:
                print(f"Skipping Azure pipeline for {item['organization']}/{item['project']} due to missing Azure token.")
                continue
                
            # Trigger the Azure DevOps pipeline
            run_id = trigger_azure_pipeline(
                item["organization"],
                item["project"],
                item["pipeline_id"],
                azure_token,
                item.get("branch", "main")
            )
            
            # Wait for the pipeline to complete if requested
            if wait_for_completion and run_id:
                print(f"Waiting for Azure DevOps pipeline {item['pipeline_id']} in {item['organization']}/{item['project']} to complete...")
                success = wait_for_azure_pipeline(
                    item["organization"], 
                    item["project"], 
                    run_id, 
                    azure_token,
                    timeout,
                    check_interval
                )
                if not success and not continue_on_error:
                    print("Stopping execution due to pipeline failure.")
                    return
            elif wait_for_completion and not run_id:
                print(f"Could not get run ID for Azure pipeline {item['pipeline_id']} in {item['organization']}/{item['project']}.")
                if not continue_on_error:
                    print("Stopping execution.")
                    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CI/CD Orchestrator")
    parser.add_argument("--config", required=True, help="Path to the configuration file")
    parser.add_argument("--github-token", required=False, help="GitHub token for authentication")
    parser.add_argument("--azure-token", required=False, help="Azure DevOps token for authentication")
    
    # Add arguments for controlling pipeline waiting behavior
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for pipelines to complete before triggering the next one")
    parser.add_argument("--timeout", type=int, default=3600, help="Maximum time to wait for each pipeline (in seconds, default: 3600)")
    parser.add_argument("--check-interval", type=int, default=30, help="Time between status checks (in seconds, default: 30)")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue with next pipeline even if the current one fails")
    
    args = parser.parse_args()
    
    main(
        args.config,
        args.github_token,
        args.azure_token,
        not args.no_wait,  # Invert the no-wait flag
        args.timeout,
        args.check_interval,
        args.continue_on_error
    )
