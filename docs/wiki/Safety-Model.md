# Safety model

Status: design. These are the rules the code has to meet, not behaviour you can run.

A model never posts directly. Everything it drafts goes through a gate first, and the gate fails closed: if the guard is unreachable, times out, or returns something that cannot be parsed, the message is dropped. Silence is the safe failure. A bot that says nothing for a minute is an inconvenience, and a bot that says the wrong thing live is a clip.

## The gate

Deterministic rules run first (length, links, mentions, a blocklist). Then a classifier runs, on a separate Ollama instance with a configurable endpoint and a latency budget. The suite already runs a local Llama Guard model for this kind of job. If any step cannot give a verdict, there is no message.

## Gate before TTS

Text is gated before it is synthesised. Once words have been spoken out loud, no platform moderation can take them back, so the only place to stop them is before the audio exists.

## Actions are an allowlist

The model can request only the actions the config names. Each is its own entry with its own limits. The first release has chat and TTS only. OBS control comes later through authenticated obs-websocket, as separate entries. A model-proposed stream action goes to a private Discord channel where the maintainer or a moderator approves it, and chat alone never triggers one.

## Chat is untrusted

Viewer text is data. It is never instructions to the engine, and it never overrides the persona or the rules. Someone will try, usually within the first hour.

## Memory and wipe commands

Memory is for linked viewers only, short facts rather than transcripts, stored locally in SQLite for 30 days since last activity. No memory goes to a cloud provider unless that provider is configured to receive it. Memory and wipe commands are restricted to the maintainer and moderators. A viewer still has to be able to delete their own stored data, and the exact split between those two is an open question in the spec.

## Things the bot does not do

- No Discord message content is used as training data or in evaluation sets. Discord's developer policy is reported to forbid it without permission, and the policy text is still to be verified. Generating a reply with an existing model is a different thing.
- No direct messages or private channels are sent to an external model.
- It does not moderate. Penguin Overlord moderates, with separate credentials, and LLMFAO does conversation and entertainment.
- It does not answer itself or another bot, and a hard cap limits consecutive bot messages.
- It responds to a command or a mention by default. Replying to arbitrary chat is a configured, rate-limited mode.

For how the gate and its neighbours get reviewed, see [How-We-Build](How-We-Build.md).
