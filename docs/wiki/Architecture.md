# Architecture

Status: design. No part of this pipeline is implemented.

An event comes in from a platform, the engine decides whether to speak, a model drafts something, a separate gate decides whether the draft may leave, and only then does an action run. That is the whole shape.

```
platform event -> adapter -> filter -> context -> model -> gate -> action -> adapter
```

1. Filter. Drop the bot's own messages, bridged echoes, anyone on the ignore list, and anything the platform marks as not for us. Then decide whether to speak at all: a mention, a command, a cooldown, or a configured chance.
2. Context. The persona, a bounded window of recent chat, and what is remembered about the speaker if they opted in. Chat text is wrapped as data and never concatenated into the instructions.
3. Model. One provider call, picked by the kind of turn (chat, gate, summary).
4. Gate. A second, separate check on the draft. It fails closed. See [Safety-Model](Safety-Model.md).
5. Action. The model can only request actions the config names: say, TTS, and later a scene change. Each is its own allowlist entry with its own limits.

## Two repositories, one rule

LLMFAO holds the logic. The platform clients and the model providers live in hypeman-social, the shared core that the other bots in the suite already use. The rule that settles every argument about placement: if a second daemon could want it, it goes in hypeman-social and LLMFAO imports it.

| Lives in hypeman-social | Lives in LLMFAO |
| --- | --- |
| Reading and sending Twitch chat, bot OAuth, token refresh, platform rate limits | Persona, memory, turn-taking |
| Discord and Matrix send and receive | The safety gate and the action allowlist |
| Ollama, Gemini, OpenAI and Claude providers and their per-provider tuning | Which provider handles which kind of turn |
| Reading secrets from Doppler | Viewer identity linking, TTS and stream automation as actions |

The reason is boring on purpose. Stream-Daemon announces on Twitch too, and a second copy of a Twitch client is a second place for a token bug. Adapters are also kept dumb: they convert events in and send text out, with no policy, no prompts and no model access. Policy lives in the engine, where the gate can see all of it.

## Platforms

Twitch first, with the whole first release being one good Twitch bot. Discord second. Matrix is reached through the mautrix bridge that already links Discord and Matrix, so there is no Matrix client to build. A native Matrix adapter may exist as scaffolding, off by default and untested, and nothing in the first release depends on it.

A bridge changes what "a message from a user" means, so the design assumes these and verifies them against the real deployment before relying on them: the bot drops its own echoes coming back across the bridge, each bridged room pair has one home platform that replies, and a bridged sender is a different trust level from a native one.

## Providers

The default is Ollama with `gemma4:12b`, local. Gemini, OpenAI and Claude are opt-in, and a fallback only happens when someone configured one. hypeman-social has Ollama and Gemini today. The OpenAI and Claude providers are new work there and are not built.
