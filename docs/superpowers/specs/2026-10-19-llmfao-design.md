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

## Live state

The bot knows whether the streamer is live. The source is Twitch EventSub `stream.online` and `stream.offline` (no
scope needed), plus Get Streams once at startup and a slow poll (every 60 to 120 seconds). The poll matters: events
missed during a connection drop are not replayed, and a bot that starts while the streamer is already live has to learn
it. State is `live`, `offline` or `unknown`, and `unknown` behaves like `offline` until it resolves.

Offline, the bot is quiet. Ambient chat, scheduled messages and recaps are off. Direct mentions and commands still get
answers, and event thank-yous (a sub, a raid) still go out at low priority, each switchable in config.

## Events, with the least privilege that works

Research against Twitch's documentation (to be re-checked against the live pages when the adapter is written) shows the
bot account's own token is enough for the core events, with no second credential:

- Subs, resubs, gifted subs and raids arrive on `channel.chat.notification`. It needs `user:read:chat` and `user:bot`
  from the bot, and the broadcaster either makes the bot a moderator or grants `channel:bot`.
- Cheers arrive as the `cheer` field on the chat message itself.
- Live state needs no scope. Follows need `moderator:read:followers`, so they are optional and off by default.
- The richer broadcaster-scoped types (`channel.subscribe`, `channel.cheer`, hype train, channel points) need the
  broadcaster to authorise the app with extra scopes. They are not needed for the first release, and nothing here asks for
  them.

All sources emit one neutral event: id, source, kind, time, actor id and name, anonymous flag, amount and currency,
tier, months, message, recipient and gift batch id. Duplicates are dropped by `(platform, kind, source_id)` with a ten
minute cache, and a community gift is collapsed with its per-recipient children. Viewer names and messages are untrusted
text: sanitised, length-capped, run through a name filter, and wrapped as data in every prompt.

## Tips: StreamElements

Tips, merch and loyalty events come from StreamElements through a hypeman-social adapter; Twitch owns subs, cheers and
raids, and StreamElements' copies of those are ignored so nothing is announced twice. Its channel JWT is a full
channel-owner credential, so the adapter prefers an OAuth2 token or an Overlay Token with narrow scopes, read through the
secrets layer, with a documented rotation. After downtime the activities history endpoint is used to resync tips.

## Queue and delivery

The model is often busy, and the bot must never be spammy. Everything outbound goes through one queue and one sender.

| Class | Examples | Queue limit and life | When full |
| --- | --- | --- | --- |
| 1 events | sub, gift, cheer, raid, tip | small, minutes | coalesce (ten gifts become one thank-you), then drop newest |
| 2 mentions | someone talks to the bot | small, seconds | drop oldest |
| 3 commands | `!recap`, `!so` | small, seconds | drop oldest |
| 4 ambient | chatter, scheduled lines | tiny, very short | drop oldest, and stop generating |

One sender drains the queue by class. It is bounded by per-user, per-feature and global cooldowns, and by the adapter's
rate limiter, which stays inside Twitch's limits with a margin. If the model times out or is unreachable, events fall
back to a canned thank-you written in the persona, and chat and ambient lines stay silent. A deep queue stops the
generation of ambient lines before it grows. The queue is in memory; a restart does not replay it.

Safety switches: a kill switch (a moderator command and a flag file), a dry-run mode that logs what it would say, and an
approval mode that posts the draft to a private Discord channel for a moderator to accept or drop. Every message still
passes the gate before it is sent.

## Recaps

A bounded, in-memory rolling buffer of recent chat feeds a recap, on demand from a moderator or the streamer, and on a
schedule while live. Ad-break recaps need an ad-break scope the bot does not hold, so the first release is schedule and
command only. The buffer is chat text, so a recap is a model output over untrusted input and goes through the gate.

## Persona

A persona is a data file the maintainer writes: name, tone, lore, topics to avoid, a do-not-say list, emotes, canned
fallback lines per event, and which feature each role may trigger (owner, moderator, VIP, subscriber, everyone). It is
validated on load and reloaded by a moderator command. It is data, never executed.

## Deployment

One container image, built and released through GYST's container workflow, base image pinned by digest, run as a
non-root user with a read-only filesystem. It holds no secret: Doppler injects them at start. The only state is an
optional SQLite volume for linked viewers and their short memory. A local health endpoint answers a container healthcheck.

- **On-prem:** a compose file beside the Ollama host, reaching it on the LAN.
- **Cloud:** the same image on a small host. Ollama stays on-prem and is reached through the Twingate ZTNA connector, so
  there is no public Ollama port. When the tunnel is down the availability contract applies: events use their canned
  fallbacks, chat stays silent, and an opt-in cloud fallback provider can take over, without per-viewer memory.

## First release, from the comparison

Comparable bots cover personas, role-gated triggers, event thank-yous, shoutouts, recaps and scheduled lines. The
first release is: the Twitch adapter and live state, the persona file, mention and command triggers with role gates,
the event reactions above, the queue with its classes, cooldowns and canned fallbacks, the gate, the kill switch,
dry-run, on-demand and scheduled recaps, and the container. Next: a follow-spike shutoff, a go-live opener, scheduled
lines that follow the topic, approval mode, short opt-in viewer memory and metrics. Later: TTS, OBS and a dashboard.
Persona text, prompts and branding of other products are not copied.

## Viewer identity

Opt-in, and the reason the project is worth building beside a community bot: a viewer links a Twitch account to a
Discord one with a command, and from then on watch time and chat activity can feed the community's roles and levels
(the MEE6 replacement work in Penguin Overlord). LLMFAO emits events and holds the link; Penguin Overlord consumes
them. Unlinking deletes what was stored. Nothing is linked by inference.

## Viewer memory and roasting

The fun part: the bot learns who it is talking to over time and teases them for it. That only works if the person said
yes, so consent is the spine of the design, and everything below is built on the decisions already made (linked and
opted-in viewers only, short facts, local storage, thirty days, moderator and streamer control).

**Consent levels, per viewer.** A viewer starts at nothing: the bot answers them like anyone else and remembers nothing
about them beyond the rolling chat buffer. `!roastme` opts them in to being remembered and teased at the light level.
`!noroast` stops roasting and stops any new memory at once, and the viewer can say it any time. A moderator or the
streamer can raise a consenting viewer's level, set it to zero, or cap it for everyone. Nobody is roasted by default,
moderators included. The bot never roasts someone on another person's say-so.

| Level | What the bot does |
| --- | --- |
| 0 | friendly, no teasing, no memory (everyone by default) |
| 1 | light teasing about gameplay, chat habits and shared gags (the opt-in level) |
| 2 | sharper banter, set by the viewer or a moderator, never above the streamer's cap |
| 3 | off unless the streamer enables it for a named viewer who asked for it |

**What it may remember.** A fixed list of fact kinds, and nothing else is ever written:

- something the viewer said they like (a game, a team, a snack), in their words
- a running gag the bot and the viewer share
- chat habits (a lurker, a night owl, an emote they spam)
- milestones the platform reported (first sub, months subscribed, a raid)
- a nickname they accepted
- how past teasing landed: counts of laughs, neutral replies and objections, not the messages

**What it never stores or uses.** Health or disability, appearance, sexuality, gender identity, religion, politics,
ethnicity or nationality, age or anything that suggests a minor, family and relationships, location, money, a real
name, and anything about someone who is not the speaker. Pronouns are used only if the viewer states them, never
guessed. The rule is enforced in code, not left to the prompt: the extractor can only emit the fact kinds above, a
deny list and the safety classifier reject the rest, and a stored fact that fails validation is dropped. A message that
suggests self-harm writes nothing and alerts the moderators.

**How it learns.** After a turn with a consenting viewer, a local model proposes facts from that viewer's own messages
only, as JSON that must match the schema. A fact is kept when the viewer said it outright or it has been seen twice.
Chat text is data: it cannot add a fact kind, change a level or issue a command.

**How it uses it.** At reply time it retrieves at most five relevant facts by kind and recency (no vector store in the
first release), hands them to the model as data with the viewer's level and the banned-topic list, and the draft goes
through the gate with a roast-specific policy: no protected characteristics, nothing sexual, no real-world harm, no
piling on. A viewer is teased at most once in ten minutes, and never twice in a row.

**It reads the room.** Laughter and emotes lift the viewer's comfort score. A "not funny", a "stop", silence after a
sharp line or a moderator's warning lowers the level, and an explicit objection ends roasting and new memory at once
and tells the moderators. The score only moves down on its own; going up takes the viewer or a moderator.

**Control and visibility.** The memory and wipe commands stay with the streamer and moderators (a viewer who wants
their data gone asks one, and `!noroast` stops everything new meanwhile). Moderators can list what is stored for a
viewer, wipe it, pause memory for a stream, and change levels. Facts expire thirty days after they were last
reinforced; the consent record lasts until it is withdrawn. Storage is local SQLite on a mounted volume with tight file
permissions. Memory never goes to a cloud provider, including when a cloud fallback is in use.

**Tests that must exist before this ships:** a fact kind outside the list cannot be written, a message with each banned
category writes nothing, a non-consenting viewer is never teased, level 3 cannot be reached without the streamer, an
objection stops roasting within one message, expiry removes facts, and wipe leaves nothing behind. The gate and the
extractor get an adversarial review like the other security-sensitive parts.

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
- Licence GPL-3.0-or-later, to keep it open.

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
   no memory sent to a cloud provider unless that provider is configured to receive it. The memory and wipe commands are
   restricted to moderators and the streamer; anyone can talk to the bot as normal. A viewer who wants their data
   removed asks a moderator, and the docs say how.
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

5. **Token storage.** A refreshed Twitch token is held in memory, and hypeman-social offers an optional callback so a
   consumer can persist it. No Doppler write credential is built into the adapter.

## Open

- Whether a rotated Twitch refresh token invalidates the old one, which decides how often a restart needs a manual
  Doppler update. To be checked against live Twitch.

Licence: GPL-3.0-or-later, decided. (AGPL-3.0 would also bind someone who runs a modified copy as a hosted service,
which GPL does not; it was raised and not taken.)
