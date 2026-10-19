# LLMFAO: Claude Code Context

An AI-powered, multi-platform interaction engine: Twitch, Discord, Matrix, TTS and stream automation behind one
event/action interface. Package `llmfao` (src layout). Licence GPL-3.0-or-later. Copyright ChiefGyk3D.
Status: design; the spec is `docs/superpowers/specs/`.

## Invariants

- **A model never posts directly.** Every outbound message passes the safety gate first, and the gate fails
  closed: an unreachable guard, a timeout or an unparseable verdict means the message is dropped, not sent.
- **Platform and provider code lives in hypeman-social, not here.** Twitch/Discord/Matrix clients, bot OAuth, rate
  limits and the Ollama/Gemini/OpenAI/Claude providers are added to hypeman-social and imported. This repo holds
  the logic: persona, memory, turn-taking, the gate, the allowlist. If a second daemon could want it, it is not ours.
- **Platform adapters are dumb.** An adapter converts events in and sends out; it holds no policy, no prompts
  and no model access. Policy lives in the engine.
- **Twitch first, Discord second.** Matrix reaches the bot through the mautrix bridge; a native Matrix adapter is
  disabled scaffolding, documented as untested. One home platform per bridged room pair; drop bridged echoes.
- **Doppler holds every secret** (read through hypeman-social's secrets layer). The bot runs as its own Twitch
  account with minimal scopes; no token, secret or key in a file, log or model context.
- **Default model: Ollama `gemma4:12b`.** Fallback to Gemini, OpenAI or Claude is opt-in and uses `is_available()`.
- **Actions are an allowlist.** The model can request only actions the config names (say, post, scene change);
  a stream automation action is never reachable from untrusted chat text.
- **Chat is untrusted input.** Viewer text is data, never instructions to the engine or the model's own rules.
- **Viewer identity is opt-in and deletable.** Nothing links a platform account to another without the person's
  command, and unlinking removes what was stored.
- **Use hypeman's `is_available()`, never `.enabled`.** Its availability contract is the lesson of an outage.
- No callsign, grid square, hostname, serial, employer name or real endpoint in any file. Tests use synthetic data.

## Model routing (agents that write this repo)

- Every Agent dispatch sets `model: "sonnet"`; Haiku only for a mechanical one-file edit with exact before/after.
- Opus only with the maintainer's OK and the reason stated, never upgraded silently.
- Text-in/text-out work (CI log digests, triage, first drafts) goes to the local LLM first; counting and grouping
  are done in code.
- Anything that touches the safety gate, auth or the action allowlist gets a Codex adversarial review before merge,
  even when CI and the Sonnet review are green.
- Copilot reviews pull requests only. Its comments are a second opinion, not a gate.
- The measured numbers behind these rules live in SAFO's `agents.yaml`; this file only states the rules.

## Standing rules

- The gate is `ci / CI green`. Run the whole suite and read its exit code; never `check | grep && push`.
- Pin every action by commit with a `# vX.Y.Z` comment, from `git ls-remote --tags`, never from memory. A tag can
  be annotated: pin the commit it points at.
- A check must be falsifiable: break what it watches, see it red, restore.
- Public-facing text is written with the chiefgyk3d-voice skill.
- Shared CI plumbing goes to GYST, not into this repo. SAFO owns the board logic.
