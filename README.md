# LLMFAO

Artificial intelligence. Natural stupidity.

LLMFAO is Large Language Model Fucking Around Online. It is an open-source, AI-powered, multi-platform interaction engine designed to bring conversational AI to livestreams, communities, and whatever other questionable integrations we come up with.

It started with a simple question: What if we gave an LLM a microphone and access to production?

Nobody said it was a good idea.

Because giving an AI access to Twitch, Discord, Matrix, TTS, and stream automation seemed like a perfectly reasonable idea.

## Status

Design. Nothing runs yet. The first commits are the repo baseline and the spec in
[`docs/superpowers/specs/`](docs/superpowers/specs/), and the code follows the plan.

## What it is going to be

- Twitch first, with its own bot account, set up and secured on purpose. Discord second. Matrix reaches the bot
  through the mautrix bridge we already run, so there is no Matrix version to build; a native Matrix adapter exists
  as scaffolding, off by default and untested. YouTube and Kick come after.
- This repo is the logic: persona, memory, when to speak, what is allowed. The platform clients and the model
  providers live in [hypeman-social](https://github.com/ChiefGyk3D/hypeman), so every daemon gets them.
- Ollama with `gemma4:12b` is the default. Gemini, OpenAI and Claude are opt-in, each tuned for what it is good at,
  and a fallback only happens when you configured one.
- Secrets live in Doppler and nowhere else.
- TTS and stream automation behind the same interface, so "say it out loud" and "switch the scene" are actions
  the engine takes, never something a platform adapter reaches for by itself.
- Every message the model wants to send passes a safety gate before it is posted, and the gate fails closed.
- Viewer identity is opt-in. A Twitch account is linked to a community account by the person, with a command,
  and unlinking deletes what was kept.

## How it is built

Same as the rest of the suite: CI and security are callers of
[git-your-ship-together](https://github.com/ChiefGyk3D/git-your-ship-together), the board is kept by
[Scrum Around and Find Out](https://github.com/ChiefGyk3D/scrum-around-and-find-out), and the agents that write it
are routed by the rules in [`CLAUDE.md`](CLAUDE.md).

## Licence

GPL-3.0-or-later. Copyright Renegade Penguin LLC.
