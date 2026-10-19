# Roadmap

The living list for LLMFAO: what is planned, in what order, and why. Issues are the source of truth for the work; this file is the ordering and the reasoning. Update it when an issue opens, closes or changes shape.

Last reviewed: 2026-10-19. Status: design, with the platform adapters in flight in hypeman-social.

**Board:** sizes, sprints and status live on the [llmfao project](https://github.com/users/ChiefGyk3D/projects/6). How it is run is in [How this project is planned](wiki/How-This-Project-Is-Planned.md). The board is defined as code in `board.yaml` and kept current by `safo --board board.yaml reconcile` from the maintainer's own `gh` login.

## How the order was chosen

1. Foundation and the engine core first, because everything else hangs off the event model, the pipeline and the queue.
2. Twitch next, since it is the first platform and the first thing a viewer can see.
3. The safety gate and LLM routing before anything speaks in a real channel. A model never posts directly, and the gate fails closed.
4. Persona, recaps and tips once there is something safe to say them with.
5. Deployment, the runbooks and the first live run: dry-run on the real channel, then the maintainer decides.
6. Discord and the bridge, then viewer identity and memory, because both need the Twitch path proven first.
7. Stream automation (TTS, OBS) is unscheduled on purpose. It is the riskiest surface and comes last.

## In flight outside this repository

Platform and provider code lives in hypeman-social, so the first sprint is partly waiting on it.

| What | Where | State |
| --- | --- | --- |
| ChatEvent and ChatReceiver | hypeman PR #94 | Merged 2026-10-19 |
| Ollama default gemma4:12b, exact num_ctx | hypeman issue #93, PR #95 | Merged 2026-10-19 |
| Twitch chat adapter, separate bot account | hypeman issue #90, PR #97 | Open |
| Discord chat receiving, bridged-message metadata | hypeman issue #91, PR #98 | Open |
| OpenAI and Claude providers | hypeman issue #92, PR #96 | Merged 2026-10-19 |
| Twitch notifications, live state, cheers | hypeman issue #99 | Not started |
| StreamElements adapter | hypeman issue #100 | Not started |

## Sprint calendar

Two-week sprints, Tuesday to Monday, eight defined. Sprint titles on the board read `S 1` to `S 8`.

| Sprint | Dates | Focus | Maintainer hours |
| --- | --- | --- | --- |
| S1 | 2026-11-03 to 11-16 | Foundation, baseline gaps, event model, bot-account runbook | 2 |
| S2 | 2026-11-17 to 11-30 | Pipeline, cooldowns, kill switch, Twitch adapter consumption, bot account | 5 |
| S3 | 2026-12-01 to 12-14 | Queue and single sender, live state, triggers, gate rules, classifier endpoint | 5 |
| S4 | 2026-12-15 to 12-28 | Event reactions, classifier, prompt-injection handling, persona format | 0 |
| S5 | 2026-12-29 to 2027-01-11 | Allowlist, provider routing, fallback, StreamElements consumption, first persona | 7 |
| S6 | 2027-01-12 to 01-25 | Gate and Twitch reviews, recaps, container, release | 0 |
| S7 | 2027-01-26 to 02-08 | Runbooks and release process, Discord and bridge rules, consent ladder, first live run | 5 |
| S8 | 2027-02-09 to 02-22 | Discord review, bridge check, identity store, fact-kind enforcement | 5 |

The maintainer has a day job and shares evenings and weekends with other boards, so his own items stay at about 3 to 7 hours a sprint. Agent items are limited by budgets and review time: at most three in flight, each in its own branch and worktree. Sizes are S about 2 hours, M about 5, L about 12 and XL about 30. There are no XL items on this board.

## Not scheduled

- **Memory and roasting, second half.** Memory expiry and wipe commands, the extractor, retrieval, the roast gate policy, the read-the-room score, the pre-ship test list and both Codex reviews do not fit in S1 to S8 without overloading the agents. They are Backlog and get a planning pass after S8, or earlier if budget allows. The design is the spec section "Viewer memory and roasting" (pull request #66).
- **Cloud variant** behind Twingate to the on-prem Ollama. Backlog until the on-prem path is live.
- **Stream automation:** TTS behind the gate with approval in a private Discord channel, and OBS through authenticated obs-websocket. Backlog.
- **Bots & socials summary rows.** Optional; nothing blocks on them.

## Waiting on the maintainer

Doppler identity (Blocked), the Twitch bot account (Blocked until the runbook and the Doppler runtime project exist), the separate classifier endpoint, the StreamElements token, the first persona, the bridge check and the first live decision. These carry Agent You.

## Parked ideas

- Follow-spike and raid-wave protection, a go-live opener and scheduled lines that follow the topic.
- Hype train and channel point reactions, and a preview and approval mode for event messages.
- Metrics (queue depth, drops, latency, tokens) and per-language personas.
- Shoutouts that use the target's public profile only.
- A long-term lore store, multi-channel hosting, a web dashboard.
- YouTube and Kick adapters, and a native Matrix adapter beyond disabled scaffolding.
- Memory in a vector store (the first release retrieves by kind and recency).
