---
gate: {"enabled": true, "require_tests": true, "require_refs": true, "test_patterns": ["pytest", "npm test", "npm run test", "pnpm test", "yarn test", "go test", "gradle test", "gradlew test", "mvn test", "cargo test", "jest", "vitest", "make test", "./manage.py test"], "code_globs": ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.kt", "**/*.java", "**/*.go", "**/*.rs", "**/*.rb"], "skip_globs": ["**/*.md", "**/*.json", "**/*.yml", "**/*.yaml", "docs/**", ".cosmos/**"]}
---

# Charter

The working agreement for this repository. Every AI session on every machine reads this first.
Edit it in a pull request; do not tell your own AI a different style.

## How we write code
- Follow the existing style of the file you are in before any personal preference.
- Small, named functions; no clever one-liners that need a comment to decode.
- Errors are handled where they can be acted on; never swallowed silently.

## How we test
- A change to behaviour comes with a test in the same change.
- Run the tests that cover the files you touched before you stop.

## How we point at things
- Refer to code as `path/to/file.py:123`, never "the function above".
- Every claim about the codebase names the file it was verified in.

## How we review our own work
- Before finishing: re-read the diff, check it against this charter, and state what was NOT tested.
- Open findings on the files you touched are addressed or explicitly deferred with a reason.
- A change to what cosmos does updates its docs in the same commit: README.md, the site (docs/index.html), the console's docs (cosmos/ui.py: sections, the Command reference, What happens by itself) and the guide in docs/ that covers it. Numbers in the docs are measured, never estimated. tests/test_membrane.py fails when a command is missing from the Command reference.

## Architecture rules
- Add rules here as decisions are made (or type `remember: …` in a session; explicit rules outrank inferred ones).
