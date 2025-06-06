# CI/CD Orchestrator

This project provides a Python-based orchestration tool to trigger CI/CD pipelines across multiple platforms, including **GitHub Actions** and **Azure DevOps**. It allows users to manage and execute workflows for various repositories and projects from a single configuration file.

## Features

- **Multi-platform Support**:
  - Trigger GitHub Actions workflows.
  - Trigger Azure DevOps pipelines.
- **Configuration Management**:
  - Centralized configuration file (`config.json`) to define workflows and pipelines.
  - Enable or disable specific workflows using the `enabled` field.
- **Token-based Authentication**:
  - Supports GitHub tokens for GitHub Actions.
  - Supports Azure DevOps Personal Access Tokens (PAT), encoded in Base64.
- **Sequential Pipeline Execution**:
  - Option to wait for each pipeline to complete before starting the next one.
  - Configure timeout and check interval for pipeline status monitoring.
  - Choose whether to continue or stop on pipeline failures.

## How It Works

1. **Configuration File**:
   - Define workflows and pipelines in the `config.json` file.
   - Specify details such as repository, workflow file, pipeline ID, branch, and whether the workflow is enabled.

2. **Script Execution**:
   - Run the `orchestrator.py` script with the required arguments:
     - `--config`: Path to the configuration file.
     - `--github-token`: GitHub token for authentication (optional if only Azure workflows are used).
     - `--azure-token`: Azure DevOps token for authentication (optional if only GitHub workflows are used).

3. **Workflow Execution**:
   - The script reads the configuration file and triggers the enabled workflows for the specified platforms.

## Usage

### Prerequisites

- Python 3.x installed.
- Install required Python packages:
  ```bash
  pip install requests
  ```

### Configuration File

The `config.json` file defines the workflows and pipelines. Example structure:

```json
{
  "workflows": [
    {
      "type": "azure",
      "organization": "onboarding-examples",
      "project": "python-example",
      "pipeline_id": 7,
      "branch": "main",
      "enabled": true
    },
    {
      "type": "github",
      "repo": "onboarding-examples-sonarqube/python-example",
      "workflow": "sonarqube-server.yml",
      "ref": "main",
      "enabled": true
    }
  ]
}
```

### Running the Script

Run the script with the appropriate arguments:

```bash
python orchestrator.py --config config.json --github-token <your_github_token> --azure-token <your_azure_devops_token>
```

- Replace `<your_github_token>` with your GitHub Personal Access Token.
- Replace `<your_azure_devops_token>` with your Azure DevOps Personal Access Token.

#### Additional Options

Control the behavior of pipeline execution with these optional arguments:

```bash
python orchestrator.py --config config.json --github-token <token> --azure-token <token> [OPTIONS]
```

Available options:
- `--no-wait`: Don't wait for pipelines to complete before starting the next one (default is to wait)
- `--timeout <seconds>`: Maximum time to wait for each pipeline in seconds (default: 3600)
- `--check-interval <seconds>`: Time between status checks in seconds (default: 30)
- `--continue-on-error`: Continue with the next pipeline even if the current one fails

### Example Output

Basic execution:
```plaintext
Triggering workflow sonarqube-server.yml in onboarding-examples-sonarqube/python-example with ref main...
Successfully triggered workflow sonarqube-server.yml in onboarding-examples-sonarqube/python-example
Triggering Azure DevOps pipeline 7 in onboarding-examples/python-example on branch main...
Successfully triggered Azure DevOps pipeline 7 in onboarding-examples/python-example
```

With wait for completion:
```plaintext
Successfully triggered workflow sonarqube-server.yml in onboarding-examples-sonarqube/python-example
Waiting for GitHub workflow sonarqube-server.yml in onboarding-examples-sonarqube/python-example to complete...
GitHub workflow sonarqube-server.yml in onboarding-examples-sonarqube/python-example status: in_progress
GitHub workflow sonarqube-server.yml in onboarding-examples-sonarqube/python-example status: in_progress
GitHub workflow sonarqube-server.yml in onboarding-examples-sonarqube/python-example status: completed
GitHub workflow sonarqube-server.yml in onboarding-examples-sonarqube/python-example completed successfully.

Successfully triggered Azure DevOps pipeline 7 in onboarding-examples/python-example
Waiting for Azure DevOps pipeline 7 in onboarding-examples/python-example to complete...
Azure DevOps pipeline run 456 in onboarding-examples/python-example state: running
Azure DevOps pipeline run 456 in onboarding-examples/python-example state: running
Azure DevOps pipeline run 456 in onboarding-examples/python-example state: completed
Azure DevOps pipeline run 456 in onboarding-examples/python-example completed successfully.
```

## Key Features in the Code

1. **GitHub Workflow Trigger**:
   - Uses the GitHub API to trigger workflows.
   - Requires a GitHub token for authentication.

2. **Azure DevOps Pipeline Trigger**:
   - Uses the Azure DevOps API to trigger pipelines.
   - Requires a Base64-encoded Azure DevOps token for authentication.

3. **Enable/Disable Workflows**:
   - The `enabled` field in the configuration file allows selective execution of workflows.

4. **Sequential Pipeline Execution**:
   - Ability to wait for a pipeline to complete before starting the next one.
   - Status monitoring with customizable timeout and check interval.
   - Configurable error handling for failed pipelines.

## Notes

- Ensure your tokens have the necessary permissions:
  - GitHub token: `repo` and `workflow` scopes.
  - Azure DevOps token: `Build` scope.
- Use environment variables or a secrets manager to securely manage tokens.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.