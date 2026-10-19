# Security Policy

## Supported versions

There is no release yet. Once there is, the latest tagged release is supported; fixes land on `main` and ship in
the next tag, and older tags are not patched.

## Reporting a vulnerability

Please report security issues **privately**, not in a public issue or pull request. Use GitHub's private
vulnerability reporting on this repository:
[Report a vulnerability](https://github.com/Renegade-Penguin/LLMFAO/security/advisories/new).

Please include what you expected, what happened and the steps to reproduce it. Do not include a real token, a
stream key or a viewer's personal details.

## What is in scope

- The engine under `src/llmfao/`: the safety gate, the action allowlist, platform adapters and their credential
  handling, and the viewer identity store.
- Anything that lets chat text reach an action the config did not allow, or lets a message be posted that the
  gate did not pass.
- Anything that links viewer accounts without the person's command, or keeps data after an unlink.

Vulnerabilities in Twitch, Discord, Matrix, Ollama or the other services it talks to belong with those projects.

## What to expect

The project has a sole maintainer. Expect an acknowledgement within a week and a fix or a written assessment as
soon as practical after that. There is no bug bounty. Reporters are credited in the changelog entry for the fix
unless they ask not to be.
