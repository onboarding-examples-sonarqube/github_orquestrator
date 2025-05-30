import json
import requests
import argparse
import base64  # Import base64 for encoding the Azure token
import time    # Import time for sleep functionality
import sys     # Import sys for exit functionality

def trigger_workflow(repo, workflow, token, ref="main"):
    print(f"\n[START] Triggering GitHub workflow: {workflow} in {repo} with ref {ref}")
    if not token:
        print("[ERROR] GitHub token is missing or invalid.")
        return

    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"ref": ref}
    print(f"[INFO] Sending POST request to {url}")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 204:
        print(f"[SUCCESS] Successfully triggered workflow {workflow} in {repo}")
        return True
    elif response.status_code == 401:
        print(f"[ERROR] Failed to trigger workflow {workflow} in {repo}: Unauthorized (Bad credentials).")
        return False
    else:
        print(f"[ERROR] Failed to trigger workflow {workflow} in {repo}: {response.status_code} - {response.text}")
        return False

def encode_azure_token(token):
    """Encodes the Azure DevOps token in Base64 format."""
    return base64.b64encode(f":{token}".encode("utf-8")).decode("utf-8")

def trigger_azure_pipeline(organization, project, pipeline_id, token, branch="main"):
    print(f"\n[START] Triggering Azure DevOps pipeline: {pipeline_id} in {organization}/{project} on branch {branch}")
    if not token:
        print("[ERROR] Azure DevOps token is missing or invalid.")
        return None

    encoded_token = encode_azure_token(token)  # Encode the token
    url = f"https://dev.azure.com/{organization}/{project}/_apis/pipelines/{pipeline_id}/runs?api-version=6.0-preview.1"
    headers = {
        "Authorization": f"Basic {encoded_token}",  # Use the encoded token
        "Content-Type": "application/json"
    }
    data = {"resources": {"repositories": {"self": {"refName": f"refs/heads/{branch}"}}}}
    print(f"[INFO] Sending POST request to {url}")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        run_id = response.json().get("id")
        print(f"[SUCCESS] Successfully triggered Azure DevOps pipeline {pipeline_id} in {organization}/{project} (Run ID: {run_id})")
        return run_id
    elif response.status_code == 401:
        print(f"[ERROR] Failed to trigger Azure DevOps pipeline {pipeline_id} in {organization}/{project}: Unauthorized (Bad credentials).")
        return None
    else:
        print(f"[ERROR] Failed to trigger Azure DevOps pipeline {pipeline_id} in {organization}/{project}: {response.status_code} - {response.text}")
        return None

def get_workflow_run_id(repo, workflow, token):
    """Get the latest run ID for a specific workflow."""
    print(f"[INFO] Retrieving latest run ID for workflow {workflow} in {repo}")
    if not token:
        print("[ERROR] GitHub token is missing or invalid.")
        return None

    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/runs"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"per_page": 1, "branch": "main"}  # Get the latest run

    print(f"[INFO] Sending GET request to {url}")
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        runs = response.json().get("workflow_runs", [])
        if runs:
            run_id = runs[0]["id"]
            print(f"[INFO] Found run ID: {run_id} for workflow {workflow}")
            return run_id
        else:
            print(f"[WARNING] No workflow runs found for {workflow} in {repo}")
    else:
        print(f"[ERROR] Failed to get workflow runs for {workflow} in {repo}: {response.status_code} - {response.text}")
    
    return None

def wait_for_github_workflow(repo, workflow, run_id, token, timeout=3600, check_interval=30):
    """Wait for a GitHub workflow run to complete."""
    print(f"[INFO] Starting to monitor GitHub workflow: {workflow} in {repo} (Run ID: {run_id})")
    if not run_id or not token:
        print(f"[ERROR] Missing run ID or token for {workflow} in {repo}")
        return False
        
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    check_count = 0
    elapsed_time = 0
    
    print(f"[INFO] Maximum wait time: {timeout} seconds, checking every {check_interval} seconds")
    while time.time() - start_time < timeout:
        check_count += 1
        elapsed_time = int(time.time() - start_time)
        
        print(f"[CHECK #{check_count}] Checking status of GitHub workflow {workflow} (elapsed: {elapsed_time}s)")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            run_data = response.json()
            status = run_data.get("status")
            conclusion = run_data.get("conclusion")
            
            print(f"[STATUS] GitHub workflow {workflow} in {repo} status: {status}, conclusion: {conclusion}")
            
            if status == "completed":
                if conclusion == "success":
                    print(f"[SUCCESS] GitHub workflow {workflow} in {repo} completed successfully after {elapsed_time} seconds.")
                    return True
                else:
                    print(f"[FAILED] GitHub workflow {workflow} in {repo} completed with conclusion: {conclusion} after {elapsed_time} seconds.")
                    return False
            else:
                print(f"[WAITING] GitHub workflow {workflow} is still running (status: {status}), waiting {check_interval} seconds...")
        else:
            print(f"[ERROR] Failed to get status for workflow {workflow}: {response.status_code} - {response.text}")
        
        time.sleep(check_interval)
    
    print(f"[TIMEOUT] Maximum wait time ({timeout}s) exceeded for GitHub workflow {workflow} in {repo}.")
    return False

def wait_for_azure_pipeline(organization, project, run_id, token, timeout=3600, check_interval=30):
    """Wait for an Azure DevOps pipeline run to complete."""
    print(f"[INFO] Starting to monitor Azure DevOps pipeline in {organization}/{project} (Run ID: {run_id})")
    if not run_id or not token:
        print(f"[ERROR] Missing run ID or token for pipeline in {organization}/{project}")
        return False
        
    encoded_token = encode_azure_token(token)
    url = f"https://dev.azure.com/{organization}/{project}/_apis/pipelines/runs/{run_id}?api-version=6.0-preview.1"
    headers = {
        "Authorization": f"Basic {encoded_token}",
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    check_count = 0
    elapsed_time = 0
    
    print(f"[INFO] Maximum wait time: {timeout} seconds, checking every {check_interval} seconds")
    while time.time() - start_time < timeout:
        check_count += 1
        elapsed_time = int(time.time() - start_time)
        
        print(f"[CHECK #{check_count}] Checking status of Azure DevOps pipeline (elapsed: {elapsed_time}s)")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            run_data = response.json()
            state = run_data.get("state")
            result = run_data.get("result")
            
            # Get pipeline name if available
            name = run_data.get("name", f"Pipeline {run_id}")
            
            print(f"[STATUS] Azure DevOps pipeline {name} in {organization}/{project} state: {state}, result: {result}")
            
            if state == "completed":
                if result == "succeeded":
                    print(f"[SUCCESS] Azure DevOps pipeline {name} in {organization}/{project} completed successfully after {elapsed_time} seconds.")
                    return True
                else:
                    print(f"[FAILED] Azure DevOps pipeline {name} in {organization}/{project} completed with result: {result} after {elapsed_time} seconds.")
                    return False
            else:
                print(f"[WAITING] Azure DevOps pipeline {name} is still running (state: {state}), waiting {check_interval} seconds...")
        else:
            print(f"[ERROR] Failed to get status for pipeline run {run_id}: {response.status_code} - {response.text}")
        
        time.sleep(check_interval)
    
    print(f"[TIMEOUT] Maximum wait time ({timeout}s) exceeded for Azure DevOps pipeline run {run_id} in {organization}/{project}.")
    return False

def process_github_workflow(item, github_token, wait_for_completion=True, timeout=3600, check_interval=30, continue_on_error=False):
    """Process a GitHub workflow item from the config."""
    repo = item["repo"]
    workflow = item["workflow"]
    ref = item.get("ref", "main")
    
    # Check if token is available
    if not github_token:
        print(f"[SKIPPED] Skipping GitHub workflow for {repo} due to missing GitHub token.")
        return True
    
    # Trigger the workflow
    trigger_success = trigger_workflow(repo, workflow, github_token, ref)
    
    # If not waiting for completion or trigger failed, return
    if not wait_for_completion:
        print(f"[INFO] Not waiting for {workflow} in {repo} to complete as --no-wait was specified.")
        return True
    
    if not trigger_success and not continue_on_error:
        print(f"[ERROR] Failed to trigger workflow {workflow}. Stopping execution.")
        return False
        
    # Wait a moment to let the API register the new run
    print(f"[INFO] Waiting 5 seconds to let the API register the new run for {workflow}...")
    time.sleep(5)
    
    # Get the workflow run ID
    run_id = get_workflow_run_id(repo, workflow, github_token)
    if not run_id:
        error_msg = f"[ERROR] Could not get run ID for workflow {workflow} in {repo}."
        print(error_msg)
        return continue_on_error
    
    # Wait for the workflow to complete
    success = wait_for_github_workflow(
        repo, 
        workflow, 
        run_id, 
        github_token, 
        timeout, 
        check_interval
    )
    
    if not success and not continue_on_error:
        print(f"[FAILURE] Stopping execution due to workflow {workflow} in {repo} failure.")
        return False
        
    return True

def process_azure_pipeline(item, azure_token, wait_for_completion=True, timeout=3600, check_interval=30, continue_on_error=False):
    """Process an Azure DevOps pipeline item from the config."""
    organization = item["organization"]
    project = item["project"]
    pipeline_id = item["pipeline_id"]
    branch = item.get("branch", "main")
    
    # Check if token is available
    if not azure_token:
        print(f"[SKIPPED] Skipping Azure pipeline for {organization}/{project} due to missing Azure token.")
        return True
    
    # Trigger the pipeline
    run_id = trigger_azure_pipeline(
        organization,
        project,
        pipeline_id,
        azure_token,
        branch
    )
    
    # If not waiting for completion or trigger failed with no run ID, return
    if not wait_for_completion:
        print(f"[INFO] Not waiting for pipeline {pipeline_id} in {organization}/{project} to complete as --no-wait was specified.")
        return True
        
    if not run_id:
        error_msg = f"[ERROR] Could not get run ID for Azure pipeline {pipeline_id} in {organization}/{project}."
        print(error_msg)
        return continue_on_error
    
    # Wait for the pipeline to complete
    success = wait_for_azure_pipeline(
        organization, 
        project, 
        run_id, 
        azure_token,
        timeout,
        check_interval
    )
    
    if not success and not continue_on_error:
        print(f"[FAILURE] Stopping execution due to pipeline {pipeline_id} in {organization}/{project} failure.")
        return False
        
    return True

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
    print("\n[START] Starting CI/CD Orchestrator")
    print(f"[CONFIG] Using configuration file: {config_path}")
    print(f"[CONFIG] Wait for completion: {wait_for_completion}, Timeout: {timeout}s, Check interval: {check_interval}s, Continue on error: {continue_on_error}")
    
    if not github_token and not azure_token:
        print("[ERROR] At least one token (GitHub or Azure DevOps) must be provided.")
        return

    try:
        print(f"[INFO] Reading configuration from {config_path}")
        with open(config_path, "r") as f:
            config = json.load(f)
            
        workflow_count = len(config.get("workflows", []))
        print(f"[INFO] Found {workflow_count} workflows/pipelines in configuration")
        
        for index, item in enumerate(config.get("workflows", []), 1):
            print(f"\n[WORKFLOW {index}/{workflow_count}] Processing: {item.get('repo', item.get('project'))}")
            
            # Skip disabled workflows
            if not item.get("enabled", True):
                print(f"[SKIPPED] Skipping disabled workflow for {item.get('repo', item.get('project'))}.")
                continue

            # Process based on the workflow type
            if item.get("type") == "github":
                success = process_github_workflow(
                    item, 
                    github_token, 
                    wait_for_completion, 
                    timeout, 
                    check_interval, 
                    continue_on_error
                )
                if not success:
                    print("[ERROR] GitHub workflow processing failed, stopping execution.")
                    return
                    
            elif item.get("type") == "azure":
                success = process_azure_pipeline(
                    item, 
                    azure_token, 
                    wait_for_completion, 
                    timeout, 
                    check_interval, 
                    continue_on_error
                )
                if not success:
                    print("[ERROR] Azure DevOps pipeline processing failed, stopping execution.")
                    return
            
            print(f"[COMPLETE] Finished processing workflow {index}/{workflow_count}")
                
        print("\n[SUCCESS] All workflows processed successfully")
            
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())

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
