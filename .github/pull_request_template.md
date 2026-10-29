issue: ChiefGyk3D/LLMFAO#

<!-- Required. Every pull request links its issue: "issue: owner/repo#N" on the first line. -->

## What and why

<!-- What changes, and why. -->

## Definition of done

- [ ] `make check` passes and `ci / CI green` is green, including the secret scan
- [ ] Tests exist for what changed, and a test that should fail without the change was shown to fail
- [ ] Docs, wiki (`docs/wiki/`) and `docs/ROADMAP.md` say what is now true, in this pull request
- [ ] No secret, callsign, hostname, employer name or real endpoint in any file; tests use synthetic data
- [ ] If it touches the safety gate, auth, the action allowlist or stored viewer data: Codex adversarial review done
- [ ] If it touches the live bot: how it is deployed and how it rolls back are stated below

## Deploy and rollback

<!-- Or "n/a: does not touch the live bot". -->

## Gaps found and not fixed here

<!-- Anything outside this issue's scope that you noticed. Link or file an issue; do not fix it silently. -->
