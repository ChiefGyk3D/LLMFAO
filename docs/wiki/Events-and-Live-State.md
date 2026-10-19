# Events and live state

Status: design. Everything below is the plan, built from reading Twitch and StreamElements documentation. The research behind it was read through a summarising fetch, so exact payload fields must be re-checked against the live docs before any code depends on them.

The bot should react to what happens on stream, and it should know whether the stream is on. Both come from the same place if you pick the sources carefully.

## Twitch, with the bot's own token

The goal is to do as much as possible with the bot account's token alone, so the streamer hands over as little as possible.

- Subs, resubs, gift subs and raids arrive through the `channel.chat.notification` EventSub type. The bot's own user token covers it, provided the bot is a moderator or the broadcaster has granted `channel:bot`. The broadcaster's `channel:read:subscriptions` is not needed. The catch is that chat notifications are less precisely structured than the dedicated sub events and only cover things that show up in chat.
- Cheers come in on the normal chat message, which carries a cheer field, so bits need no extra scope when read that way.
- Raids can also be subscribed to directly, with no authorisation required.
- Richer sub and cheer events, hype trains and channel point redemptions need the broadcaster to authorise the app with extra scopes. Those are optional. Whether a bot's token can create those subscriptions when the broadcaster authorised the same app separately is unverified.
- Follows need a moderator scope on a bot that is a moderator, or can come from StreamElements instead.

## Knowing you are live

`stream.online` and `stream.offline` need no authorisation. On startup the bot opens the WebSocket, creates its subscriptions, and then asks Get Streams whether the channel is live. Subscribing first and querying second avoids a gap, and a stale poll must not overrule a newer offline event. The Get Streams details were read only from a search summary and are unverified. A periodic poll every minute or two is the planned fallback.

Twitch does not replay events lost while a connection was down. The bot recreates its subscriptions on a fresh session and does not try to reconstruct what it missed.

## Tips

Twitch has no tips, so StreamElements is the source. Its realtime gateway and its tips and activities topics are documented, but the old Socket.IO connection's status, the OAuth route, the rotation of the channel token, and the terms of use were not verified. Treat the channel token as a full owner credential, a password, and prefer a scoped token when one is available. Each streamer brings their own, and none ships in the repository.

## Deduping

Two sources can announce the same thing. The plan: key each event on source, kind and the source's own id, keep a ten-minute cache plus a persistent cursor, and prefer the Twitch copy for subs. A community gift arrives as a batch followed by one event per recipient, so the batch is announced once and the children are suppressed. Events carry a normalised shape (kind, actor, amount, tier, message), and the message field is treated as untrusted text like any other chat.

What happens to these events once they arrive is on [Queue-and-Rate-Limits](Queue-and-Rate-Limits.md).
