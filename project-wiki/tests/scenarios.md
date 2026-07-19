# Project Wiki Forward Scenarios

## Empty Repository

`init` creates one supported skeleton, records evidence gaps, and invents no product, module, command, storage, or flow claims.

## Existing Repository

`init` derives purpose, stack, commands, modules, state owners, flows, and traps from tracked source, manifests, tests, and current docs. `read` starts from the root map and opens only directly relevant evidence.

## Dirty Worktree

`update` records dirty state, considers staged and working changes, preserves unrelated user changes, and never labels the map as verified at a commit that does not contain those changes.

## Unmapped Diff

A changed path with no defensible map relationship becomes an explicit verification gap. It is not assigned to a guessed module or used to trigger a broad rewrite.

## Added Modified And Deleted Paths

`update` adds only source-supported claims for new paths, rechecks only affected claims for modified paths, and removes claims only after source deletion is verified. Unverifiable claims become stale.

## Stale Or Missing Base Ref

`update` validates the requested base. It uses a proven merge-base when available; otherwise it records the comparison gap and does not claim complete coverage.

## Topic Split

One root file remains the default. `add` writes to the root first. A topic is split only when the root would exceed 8 KB, or the topic exceeds 40 lines and is repeatedly read. Initialization never creates a fixed page set.

## Sensitive Evidence

Secrets, credentials, cookies, tokens, personal data, payloads, and reversible private URLs are omitted or irreversibly sanitized.

## Source Deletion

Verified source deletion permits removal of the obsolete map claim. Unverified absence marks the claim stale instead of preserving a permanent removed-entry ledger.
