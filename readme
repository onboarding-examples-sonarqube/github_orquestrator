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

### Example Output

```plaintext
Triggering workflow sonarqube-server.yml in onboarding-examples-sonarqube/python-example with ref main...
Successfully triggered workflow sonarqube-server.yml in onboarding-examples-sonarqube/python-example
Triggering Azure DevOps pipeline 7 in onboarding-examples/python-example on branch main...
Successfully triggered Azure DevOps pipeline 7 in onboarding-examples/python-example
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

## Notes

- Ensure your tokens have the necessary permissions:
  - GitHub token: `repo` and `workflow` scopes.
  - Azure DevOps token: `Build` scope.
- Use environment variables or a secrets manager to securely manage tokens.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.