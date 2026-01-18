# Workflow and Automation Policy

## Overview

This repository follows a **manual-execution-only policy** for all GitHub Actions workflows and automated processes.

## Policy Statement

**No automated workflows or processes should run without explicit manual triggering.**

## Scope

This policy applies to:

### 1. GitHub Actions Workflows
- ✅ All workflows must use `workflow_dispatch` trigger only
- ❌ No automatic triggers on: `push`, `pull_request`, `pull_request_target`, `merge_group`, `schedule`
- ❌ No workflows should run on PR open, update, or merge
- ❌ No workflows should run on commits or branch pushes

### 2. GitHub Copilot Reviews
- ✅ Request Copilot reviews manually when needed
- ❌ No automatic Copilot review triggers on PR events

### 3. Other Automated Processes
- ❌ No scheduled/cron jobs
- ❌ No automatic deployment triggers
- ❌ No automatic dependency updates (e.g., Dependabot auto-merge)

## Implementation Guidelines

### For Workflow Authors

When creating or modifying workflows:

1. **Only use `workflow_dispatch` trigger:**
   ```yaml
   on:
     workflow_dispatch:
   ```

2. **Add input parameters for context:**
   ```yaml
   on:
     workflow_dispatch:
       inputs:
         reason:
           description: 'Reason for running this workflow'
           required: false
   ```

3. **Document the workflow purpose** in the workflow file comments

### For Contributors

- Do not add automatic triggers to existing workflows
- Test workflows manually using GitHub UI or CLI
- Document any workflow changes in PR descriptions

### For Maintainers

- Review workflow changes carefully during PR reviews
- Ensure all workflows follow the manual-execution policy
- Reject PRs that introduce automatic triggers

## Running Workflows Manually

### Via GitHub UI
1. Go to the "Actions" tab
2. Select the workflow from the left sidebar
3. Click "Run workflow" button
4. Fill in any required inputs
5. Click "Run workflow" to execute

### Via GitHub CLI
```bash
gh workflow run <workflow-name>
```

### Via GitHub API
```bash
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/munaimtahir/radreport/actions/workflows/<workflow-id>/dispatches \
  -d '{"ref":"main"}'
```

## Rationale

This policy provides:

1. **Resource Optimization**: Run CI/CD only when necessary, reducing compute costs and carbon footprint
2. **Explicit Control**: Full visibility and control over when automated processes execute
3. **Flexibility**: Developers decide when to run tests, builds, and deployments
4. **Cost Management**: Avoid unnecessary workflow runs on every commit or PR

## References

- Workflow configuration: `.github/workflows/README.md`
- Example template: `.github/workflows/example-manual-workflow.yml.template`
- GitHub Actions documentation: https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch

## Questions or Concerns

If you have questions about this policy or need an exception, please open an issue for discussion.
