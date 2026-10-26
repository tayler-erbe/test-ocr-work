# Resync after the personal repository history rewrite

The personal repository's 14 branch histories were rewritten on 26 October 2026 to remove project-specific identity and private-derived pilot reports. Branch names were retained. Commit IDs changed. The institutional repository was not rewritten.

Public benchmark payloads, approved exports and frozen scorers were preserved. Across the 14 branch heads, 1,650 public file references were checked with no content changes. The current main tree was identical before adding this resync note and the new public confirmation results.

## For another checkout or coding assistant

1. Stop pushing from an old checkout. Do not pull/merge the old and rewritten histories together.
2. Preserve uncommitted work outside the checkout. Do not delete an old folder containing work you need.
3. Clone a new working directory:

   ```powershell
   git clone https://github.com/tayler-erbe/test-ocr-work.git C:\dev\test-ocr-work-fresh
   git -C C:\dev\test-ocr-work-fresh lfs pull
   ```

4. Read AGENTS.md and the current README. Run `python tools/check_project.py --data` from the fresh checkout with the documented dependencies.
5. Reapply only reviewed, public-safe code changes from any saved local work. Do not merge, push or cherry-pick old branches wholesale: that can restore removed material. Validate the resulting tree before publishing.
6. Use the existing branch names only after fetching their rewritten versions into the fresh clone. Frozen experiment commit IDs in immutable provenance records remain historical identities; a local recovery record maps them to rewritten commits.

A verified recovery bundle and the original commit mapping are stored outside the repository on the work machine. They must not be uploaded. Older local worktrees are retained for recovery; their push URL is disabled to prevent accidental restoration of the removed history.

## Publication limits

This cleans reachable branch history. It cannot erase other people's clones, earlier downloads, host caches or unreachable server objects. Repository visibility stays private. Review platform-held copies before changing visibility; see [GitHub's history-removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
