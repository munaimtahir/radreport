# GitHub Actions Workflows Policy

## Manual Workflow Execution Only

**All workflows in this repository are configured for manual execution only.**

### Policy

- No workflows should run automatically on:
  - Push events
  - Pull request events (open, synchronize, reopen, etc.)
  - Merge events
  - Commit events
  - Schedule/cron events
  
### Workflow Trigger Configuration

All workflows must use `workflow_dispatch` as their only trigger:

```yaml
on:
  workflow_dispatch:
```

### Running Workflows

Workflows should be triggered manually through:
- GitHub UI: Actions tab → Select workflow → Run workflow button
- GitHub CLI: `gh workflow run <workflow-name>`
- GitHub API

### GitHub Copilot Reviews

GitHub Copilot code reviews should also be requested manually when needed, not automatically on PR events.

### Rationale

This policy ensures:
- Full control over when CI/CD processes run
- Resource optimization by running workflows only when necessary
- Explicit intent for all automated processes
