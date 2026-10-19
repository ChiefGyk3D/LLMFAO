# How we build

Status: this one is current. It describes how the repository is run today, even though the product is still design.

- CI and security are callers of reusable workflows in git-your-ship-together, pinned by commit with a version comment. The gate that branch protection watches is `ci / CI green`. This wiki publishes through the same repository's wiki workflow.
- The board is the Bots and socials project, kept in step with issues by project-sync and the Scrum Around and Find Out playbook.
- Agents that write code are routed by rules in the repo's `CLAUDE.md`: Sonnet by default, Haiku for mechanical one-file edits, and Opus only with the maintainer's say-so and a stated reason.
- Anything touching the gate, auth or the action allowlist gets an adversarial review before merge, even when CI and an ordinary review are green.
- No test calls a live API. Platform and model behaviour is faked, and the data is synthetic.
- A check has to be falsifiable: break the thing it watches, see it go red, restore it. The wiki generator's tests were written that way.
- Pull requests get a Copilot review as a second opinion. It is not a gate.

Platform clients and model providers are built in hypeman-social first and released before this repository depends on them. See [Architecture](Architecture.md).
