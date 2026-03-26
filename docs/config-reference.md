# Config Reference

All placeholders available in `.codecannon.yaml`. Each is substituted into skill files by `sync.sh`.

For the canonical source, see [`config.schema.yaml`](../config.schema.yaml).

## Branch names

| Key | Default | Used in | Description |
|---|---|---|---|
| `BRANCH_PROD` | `main` | ship, deploy | Production branch. All release promotion targets this branch. |
| `BRANCH_DEV` | *(empty)* | ship, deploy, qa, review-agent | Development/integration branch. Leave empty for trunk-based development. Set to enable two-branch mode. |
| `BRANCH_TEST` | *(empty)* | deploy | Test/staging branch for three-branch workflows. Requires `BRANCH_DEV` to be set. |

See [branching models](branching.md) for how these values change skill behavior.

## Workflow commands

| Key | Default | Used in | Description |
|---|---|---|---|
| `CHECK_CMD` | `make check` | ship | Type-check / lint gate that must pass before shipping. |
| `DEV_CMD` | `make dev` | start | Start the local development server. Suggested to user after `/start` writes code. |
| `ABANDON_CMD` | `make abandon` | start | Discard all changes and delete the current feature branch. |
| `MERGE_CMD` | `make merge` | ship, deploy | Merge the current feature PR into the integration branch. |
| `DEPLOY_PREVIEW_CMD` | `make deploy-preview` | deploy | Deploy to the pre-production environment. |
| `DEPLOY_PROD_CMD` | `make deploy-prod` | deploy | Deploy to production. |
| `REVIEW_GATE` | `ai` | ship, review | Controls AI review in `/ship`. Values: `ai` (blocks on critical findings), `advisory` (posts but doesn't block), `off` (no review). |

## Version bumping

| Key | Default | Used in | Description |
|---|---|---|---|
| `VERSION_READ_CMD` | `node -p "require('./package.json').version"` | deploy | Command that prints the current version string. |
| `BUMP_PATCH_CMD` | `make bump-patch` | deploy | Bump patch version, commit, and tag. |
| `BUMP_MINOR_CMD` | `make bump-minor` | deploy | Bump minor version, commit, and tag. |
| `BUMP_MAJOR_CMD` | `make bump-major` | deploy | Bump major version, commit, and tag. |
| `SET_VERSION_CMD` | `make set-version V=` | deploy | Set an arbitrary version (value appended as argument). |

## Paths

| Key | Default | Used in | Description |
|---|---|---|---|
| `REVIEW_AGENT_PROMPT` | `.claude/review-agent-prompt.md` | ship, review, review-agent | Path to the review agent prompt file. |

## GitHub / PR settings

| Key | Default | Used in | Description |
|---|---|---|---|
| `DEFAULT_REVIEWERS` | *(empty)* | ship | Comma-separated GitHub handles or team slugs to add as PR reviewers. |
| `TICKET_LABELS` | *(empty)* | start | Comma-separated label pool the agent may apply to new issues. The agent selects 1-3 fitting labels, not all of them. |
| `TICKET_LABEL_CREATION_ALLOWED` | `false` | start | Whether the agent may create new GitHub labels when no pool label fits. |
| `DEFAULT_MILESTONE` | *(empty)* | start | Milestone applied to every new issue. Overrides auto-detection from GitHub. |
| `QA_READY_LABEL` | `ready-for-qa` | ship, qa | Label applied by `/ship` in two-branch mode when a feature merges to `BRANCH_DEV`. |
| `QA_PASSED_LABEL` | `qa-passed` | qa | Label applied by `/qa` when a feature passes QA. |
| `QA_FAILED_LABEL` | `qa-failed` | qa | Label applied by `/qa` when a feature fails QA. |

## Review agent content

| Key | Default | Used in | Description |
|---|---|---|---|
| `PLATFORM_COMPLIANCE_NOTES` | *(HTML comment placeholder)* | review-agent | Platform-specific compliance rules injected into the review agent prompt. Use a YAML block scalar for multi-line content. |
| `CONVENTIONS_NOTES` | *(HTML comment placeholder)* | review-agent | Project-specific conventions injected into the review agent prompt. Use a YAML block scalar for multi-line content. |

See the [customization guide](customization.md) for examples of setting these values.

## Top-level config

In addition to the `config:` block, `.codecannon.yaml` has a top-level `adapters:` key:

```yaml
adapters:
  - claude
  - cursor
```

This controls which agent adapters `sync.sh` generates files for. See [adapters](adapters.md) for details on each.
