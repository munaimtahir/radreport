# Spec Lint Utility

`specLint.ts` is a developer-only utility that ensures your Enhanced UI specifications (`TemplateUiSpec`) remain synchronized with the underlying JSON schemas.

## Why use it?
When a backend template schema changes (fields renamed, removed, or types changed), the UI spec might reference keys that no longer exist. This leads to broken visibility rules or missing enhancements.

## What it validates:
1. **Unknown Keys in Enhancements**: Warns if `fieldEnhancements` references a key not in the schema.
2. **Broken Visibility Rules**: Warns if `when.key`, `hide`, or `show` keys are missing from the schema.
3. **Paired Group Prefixes**: Warns if a prefix (e.g., `kid_r_`) doesn't match a single field in the schema.

## How to use:
1. It runs **automatically** in `ReportingPage.tsx` when `import.meta.env.DEV` is true.
2. Open your browser console (F12).
3. Look for grouped warnings starting with `[SpecLint]`.

## Deployment:
The linting logic is wrapped in `import.meta.env.DEV` checks, so it will be eliminated (or become a no-op) during production builds, ensuring zero performance impact for end users.
