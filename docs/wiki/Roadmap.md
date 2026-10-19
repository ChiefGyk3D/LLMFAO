# Roadmap

Status: design. This is a plan, ordered by what a first useful Twitch bot needs. It was shaped by looking at comparable bots, and none of the feature names are borrowed.

## MVP

- A separate bot account that reads chat and posts through the platform's send API (see [Twitch-Bot-Account](Twitch-Bot-Account.md)).
- A persona file with tone, lore, a do-not-say list and per-feature instructions.
- Triggers: mentions and replies, plus a small set of commands, each with a permission level.
- Event reactions for subs, resubs, gift subs, cheers, raids and follows, with names and text sanitised, and tips from StreamElements.
- The priority queue, cooldowns and live-state handling from [Queue-and-Rate-Limits](Queue-and-Rate-Limits.md).
- Chat recaps on request and on an interval, from a rolling buffer.
- The gate, a kill switch, dry-run mode, and an output filter for length, links and mention spam.
- A local model with a timeout and a fallback to silence or a canned line.

## Next

- Protection against follow spikes and raid waves.
- Scheduled messages that adapt to what is happening, and a go-live opener.
- Hype train and channel point reactions.
- Short, opt-in, deletable viewer memory.
- A preview and approval mode for event messages.
- Per-language personas and metrics: queue depth, drops, latency, tokens.
- Event ingestion from other tip and alert services.

## Later

- TTS and stream overlay output, behind the allowlist.
- Shoutouts that use the target's public profile only.
- A long-term lore store, multi-channel hosting, a web dashboard.
- Discord as a native adapter, then YouTube and Kick.

Items move between tiers as the build teaches us things. Comparable products exist, and the gaps in what they document (scopes, memory, queueing, offline behaviour) are where we put effort. That claim comes from reading their public pages and not from using them.
