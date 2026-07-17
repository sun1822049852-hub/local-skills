---
name: semantic-regression-guard
description: Use when changing fallback logic, data-source selection, aggregation, route response shaping, or UI-facing summary fields where behavior can silently downgrade while existing tests still pass.
---

# Semantic Regression Guard

## Overview
This skill prevents "tests green but product meaning regressed" changes.

Core rule: treat **data precision downgrade** as a behavior break, not an implementation detail.

## When to Use
- A field keeps the same name but now comes from a different source
- A fallback path is added or widened
- Runtime data and stats/aggregation data are mixed
- UI still renders, but the displayed meaning may have become coarser
- Existing tests mostly assert counts, status codes, or presence, not semantic precision

Do not use for pure styling changes with no data or behavior impact.

## Guard Checklist
Before changing code, freeze these four things in writing:
- What exact user-visible meaning this field/view currently carries
- Which source is the truth source
- Which fallback sources are allowed
- What precision loss is forbidden

Typical forbidden downgrade examples:
- `account + mode` -> `mode only`
- exact source list -> aggregated count bucket
- live runtime state -> stale daily summary presented as live detail

## Implementation Rules
- Do not reuse the same field name for two different semantic levels.
- If a generic summary must coexist with an exact source list, split names explicitly.
  - Good: `source_mode_counts` vs `recent_hit_sources`
  - Bad: both called `source_mode_stats`
- If precise data is unavailable, prefer empty/unknown over fake precision.
- Any fallback that changes information granularity is `risky` by default.

## Test Floor
For each such change, require all of the following:
- One contract test on the real route/use case, not only frontend mocks
- One negative test proving generic fallback does not masquerade as precise data
- One happy-path test proving precise data still survives when present

If frontend tests and backend contract tests disagree, trust the backend contract gap first.

## Review Questions
- Did this change preserve counts but downgrade meaning?
- Can the UI still render while telling a less precise story?
- Did a fallback widen the source without widening the schema?
- Are we protecting the old bug by updating tests to the degraded output?

## Completion Standard
Do not report only "existing regression passed".
Report separately:
- existing tests passed
- new semantic guard tests added
- whether real route/real payload verification was run

## Common Failure Pattern
- A page originally uses runtime overlay with exact source info
- Later someone adds stats fallback to preserve numbers after stop/restart
- Stats store only has aggregated buckets
- UI label formatter survives unchanged
- Result: no crash, tests mostly green, user-visible meaning regresses

When you see this pattern, cut the fake fallback first, then decide separately whether to upgrade persistence.
