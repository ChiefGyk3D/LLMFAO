# Contributing to LLMFAO

LLMFAO is at the design stage. Issues, corrections to the spec and small, focused pull requests are welcome.

**A security problem does not go in a public issue.** Use the private report link in [`SECURITY.md`](SECURITY.md).

## Before you write anything

1. **Start from an issue.** Every change has one. Use the Task template (reason, done when, gate, what it waits on)
   or the Bug template. Open the issue first and wait for a reply if the change is large.
2. **Read [`CLAUDE.md`](CLAUDE.md).** It holds the invariants (a model never posts directly, the safety gate fails
   closed, chat is untrusted input, platform code lives in hypeman-social) and the rules for the agents that help
   write this repo. A change that breaks an invariant will not merge. Human contributors follow the same rules.
3. **Check the plan.** [`docs/wiki/How-This-Project-Is-Planned.md`](docs/wiki/How-This-Project-Is-Planned.md) has the
   definitions of ready and done.

## Making the change

- Branch from `main`; one issue per branch and per pull request.
- Write the test first and watch it fail without your change.
- Set up once with `make venv`, and enable the secret-scan hook with `git config core.hooksPath .githooks`.
- Run `make check` (ruff, mypy `--strict`, pytest) and read its exit code before you push.
- Use synthetic data in tests and docs. No tokens, callsigns, hostnames, employer names or real endpoints, anywhere.
- American English.

## The pull request

The template asks for an `issue: ChiefGyk3D/LLMFAO#N` line on top; a pull request without one is not reviewed.
The gate is `ci / CI green`. A change to the safety gate, auth, the action allowlist or stored viewer data also gets
an adversarial review before merge, even when CI is green. Copilot comments are a second opinion, not a gate.
If you notice a problem outside your issue, list it in the pull request instead of fixing it there.

## Labels and the board

Labels are listed in [`.github/labels.yml`](.github/labels.yml) and applied by `scripts/sync-labels.sh`. The board
is kept from `board.yaml` by SAFO, so sprint, size and area are set by the maintainer, not by you.

## License

By contributing you agree your work is released under GPL-3.0-or-later, the license of this repository.
