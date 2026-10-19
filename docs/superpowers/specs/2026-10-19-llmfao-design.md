# LLMFAO design

Status: draft for the maintainer's review, 2026-10-19. Nothing here is built.

## What it is, and what it is not

LLMFAO is the logic behind a conversational bot: who it is, what it remembers, when it speaks, what it is allowed
to do, and whether a message may go out. It is not a platform client and not an LLM client. Both of those belong in
[hypeman-social](https://github.com/ChiefGyk3D/hypeman), the shared core the suite's daemons already use.

The rule that decides every placement question: **if a second daemon could want it, it goes in hypeman-social.**
LLMFAO imports it. A feature that only makes sense with a persona, a memory or a policy stays here.

| Concern | Lives in | Why |
| --- | --- | --- |
| Reading and sending Twitch chat, bot OAuth, token refresh, rate limits | hypeman-social | Stream-Daemon announces on Twitch too |
| Discord and Matrix send/receive | hypeman-social | already there for announcements, extended for receive |
| Ollama, Gemini, OpenAI and Claude providers and their per-provider tuning | hypeman-social | every daemon's LLM layer |
| Secrets (Doppler first) | hypeman-social `config.secrets` | already there |
| Persona, memory, turn-taking, the safety gate, the action allowlist | LLMFAO | this is the product |
| Viewer identity linking | LLMFAO | needs the community side to be useful, see below |
| TTS and stream automation | LLMFAO | actions the engine takes, behind the allowlist |

## Platform order

1. **Twitch first.** The whole first release is a good Twitch bot.
2. **Discord second.** A native Discord adapter, using hypeman-social's Discord support.
3. **Matrix: through the mautrix bridge, not a Matrix client of our own.** The suite already runs a mautrix bridge
   between Discord and Matrix. So the bot lives in Discord and Matrix users reach it through the bridge. LLMFAO still
   carries scaffolding for a native Matrix adapter, **disabled by default and documented as untested**, so the day the
   bridge is the wrong answer there is a place to start. Nothing in the first release depends on it.
4. YouTube and Kick after that, as hypeman-social adapters (Stream-Daemon already knows both).

### Being mindful of the bridge

A bridge changes what "a message from a user" means. These are the behaviours the engine has to handle, written as
assumptions to verify against the real deployment before anything relies on them:

- **Echo loops.** The bot's own Discord reply crosses the bridge to Matrix, and a bridged copy can come back as a new
  event. The engine drops anything authored by its own identity, by the bridge's ghost user for its own identity, and
  anything with a message id it already sent.
- **Double replies.** If the bot sat in both a Discord channel and its bridged Matrix room, one human message would be
  seen twice. Each bridged room pair has one **home platform**; only the home adapter replies. Config names the home.
- **Who spoke.** A message from a bridged Matrix user arrives in Discord as a relayed one (a webhook or ghost), and the
  reverse in Matrix. The adapter marks such messages as `bridged=true` with the original sender where the bridge
  exposes it. Identity linking and moderation treat a bridged sender as a different trust level from a native one.
- **Formatting.** What survives the bridge differs per side (mentions, embeds, replies). Replies are plain text with
  no platform-specific markup unless the adapter for that platform supplies it.

## The Twitch bot account

The bot is **its own Twitch account**, never the broadcaster's, and it is the one thing in the project that must be
set up carefully.

- A separate account with its own email address, two-factor authentication on, and a name that says it is a bot.
- Its own Twitch application (client id and secret), not shared with another tool.
- Scopes are the smallest set that works. The current expectation is reading chat, sending chat, and acting as a bot
  in a channel the broadcaster has authorised; the exact scope names and the broadcaster's grant step are verified
  against Twitch's documentation when the adapter is written, not taken from this paragraph.
- Moderator status is granted by the broadcaster deliberately and only if a feature needs it (for example timeouts).
  Moderation actions are separate allowlist entries, off by default.
- Tokens, the client secret and refresh tokens live in Doppler. Nothing is written to the repository, a log, a crash
  report or the model's context. The bot's token is validated on the schedule Twitch requires and a failure raises an
  alert instead of retrying forever.
- Rate limits are respected by the hypeman-social adapter with a margin; the engine never sends faster than the adapter
  allows and treats "the adapter said no" as a normal outcome.
- There is a documented **revoke path**: how to disconnect the application, rotate the secret, and bring the bot back
  up, written before the first live run.
- The bot says it is a bot, in its profile and, when asked, in chat.

## Providers

Default: **Ollama with `gemma4:12b`** through hypeman-social, local, zero cost. Fallback is opt-in and follows
hypeman's rule: it never happens unless configured, and the primary is retried and takes over again when it heals.
The other providers are first-class, not afterthoughts:

| Provider | Role | Optimisations this design expects (each verified when built) |
| --- | --- | --- |
| Ollama | default | send exactly the `num_ctx` the model is loaded with; `think=false` for chat turns; a short `keep_alive` for anything that is not the resident model; never assume the GPU is free, it is shared |
| Gemini | opt-in fallback, large-context jobs | respect the tier's request limits; use context caching for a long persona |
| OpenAI | opt-in | structured output for the gate's verdict so a parse failure is a refusal, not a guess |
| Claude | opt-in | prompt caching on the persona and rules block, which is identical every turn; a small model for the gate, a larger one only for turns that earn it |

A provider's tuning is hypeman-social's to hold, because the next daemon gets it for free. LLMFAO chooses *which
provider handles which kind of turn* (chat, gate, summary) in config. hypeman-social has Ollama and Gemini today;
**OpenAI and Claude providers are new work there.**

## The pipeline

```
platform event -> adapter (hypeman-social) -> engine: filter -> context -> model -> gate -> action -> adapter
```

1. **Filter.** Drop the bot's own messages, bridged echoes, anyone on the ignore list, and anything the platform
   marks as not for us. Decide whether to speak at all (mention, command, cooldown, or a configured chance).
2. **Context.** Persona, a bounded window of recent chat, and what is remembered about the speaker if they opted in.
   Chat text is wrapped as data. It is never concatenated into the instructions.
3. **Model.** One provider call, chosen by turn type.
4. **Gate.** A second, separate check on the draft: a safety classifier (the suite already runs a local Llama Guard
   model) plus rules (length, links, mentions, blocklist). **Fails closed**: unreachable, timed out or unparseable
   means nothing is sent.
5. **Action.** The model can only ask for actions in the config's allowlist: say, TTS, and later a scene change. Each
   is its own entry with its own limits. An action that touches the stream is never reachable from a viewer's text
   alone; it needs a trusted sender or a human confirm.

## Viewer identity

Opt-in, and the reason the project is worth building beside a community bot: a viewer links a Twitch account to a
Discord one with a command, and from then on watch time and chat activity can feed the community's roles and levels
(the MEE6 replacement work in Penguin Overlord). LLMFAO emits events and holds the link; Penguin Overlord consumes
them. Unlinking deletes what was stored. Nothing is linked by inference.

## Secrets

Doppler is the secret store, read through hypeman-social's secrets layer. The repository holds names only. CI uses
the shared `ci` config over OIDC like every other repo; runtime secrets live in a separate runtime project, never in
the CI one.

## Delivery and process

- CI and security are GYST callers, pinned by commit, with the gate `ci / CI green`. The baseline is applied at
  creation, not after.
- The board is the Bots & socials project, kept by GYST's `project-sync` and SAFO. Epics become issues there.
- Agents are routed by the rules in `CLAUDE.md`; anything touching the gate, auth or the allowlist gets an adversarial
  review before merge.
- Licence GPL-3.0-or-later, like the other Renegade Penguin repositories.

## Work list outside this repository

hypeman-social needs, in this order: a Twitch chat adapter (receive and send, bot token handling, rate limits); chat
*receive* on the Discord adapter; OpenAI and Claude providers; `gemma4:12b` as the Ollama default. Each is a hypeman
issue and a release before LLMFAO depends on it.

## Decisions (2026-10-19)

1. **Name.** LLMFAO is Large Language Model Fucking Around Online. The full expansion stays in the README and
   branding. The Twitch account, the Discord application and the bot's display name are plain "LLMFAO", because
   Discord's developer policy asks applications not to promote vulgar content in their portal settings and a public
   listing is held to more than a private server. (A secondhand reading of the platforms' policies, to be checked
   against Twitch's and Discord's current text before any public listing.)
2. **Gate.** Deterministic rules first, then a classifier on a separate Ollama instance, endpoint configurable, with a
   latency budget; it fails closed. Penguin Overlord will moderate Twitch and Discord itself. LLMFAO does
   entertainment and conversation, never moderation, and the two stay separate roles with separate credentials.
3. **Memory.** Linked viewers only, short facts rather than transcripts, local SQLite, 30 days since last activity,
   no memory sent to a cloud provider unless that provider is configured to receive it. Who may trigger memory and wipe
   commands is under "Open" below.
4. **Stream automation.** The first release has TTS and chat only. OBS comes later through authenticated
   obs-websocket, as separate allowlist entries. A model-proposed action goes to a **private Discord channel** where
   the maintainer or a moderator approves it. Chat alone never triggers one.

## Rules added from review

- **Gate before TTS.** Text is gated before it is synthesised. Once it has been spoken, a platform's own moderation
  cannot take it back.
- **Cooldowns and no self-reply.** Per-user and global rate limits, a hard cap on consecutive bot messages, and the
  bot never answers itself or another bot.
- **Invoked, not omnipresent.** The bot responds to a command or a mention by default. Replying to arbitrary chat is a
  configured, rate-limited mode.
- **Discord message content is never training data.** Discord's developer policy is reported to forbid using
  API-obtained message content to train models without permission. Nothing LLMFAO sees on Discord is used for
  fine-tuning or evaluation sets, and the same rule covers any future Penguin Overlord moderation tuning that would
  read from this bot. Generating a reply with an existing model is a different thing. Verify the policy text.
- **No private messages to external models.** Direct messages and private channels are not sent to a cloud provider.

## Open

- **Who may trigger what.** Memory and wipe commands, and which bot features, are restricted to the maintainer and
  moderators. A viewer must still be able to delete their own stored data, so the exact split needs confirming.

Licence: GPL-3.0-or-later, decided. (AGPL-3.0 would also bind someone who runs a modified copy as a hosted service,
which GPL does not; it was raised and not taken.)
