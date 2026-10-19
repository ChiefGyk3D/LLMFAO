# Queue and rate limits

Status: design. Nothing here is implemented, and the numbers are starting points to be measured, not settings.

A busy stream can hand the bot a raid, a gift-sub wave and fifty mentions in the same ten seconds, while the model server is also doing something else. The queue decides what gets a reply and what quietly does not.

## Priority classes

From most to least important: events, direct mentions, commands, ambient chat. Each class has its own bounded queue.

- Events (subs, raids, tips) are coalesced rather than dropped where they can be. A wave of gift subs becomes one thank-you.
- Chat mentions, commands and ambient messages drop the oldest first when the queue is full, because a late answer to an old message is worse than none.
- Every item has a time to live, somewhere in the range of thirty to sixty seconds. Older than that, it is discarded without a model call.

## Cooldowns

Per user, per feature, and one global message budget, all kept well inside what Twitch allows. Twitch's documented limits are 20 messages per 30 seconds for an ordinary account and 100 for a broadcaster or moderator, with one message per second per channel, and going over gets the bot's messages ignored for an hour. The bot stays under that on purpose and treats "the adapter said no" as a normal result. A cap on consecutive bot messages and a rule against replying to itself sit on top.

## Offline behaviour

When the stream is offline, ambient chat and recaps are off. Direct mentions can stay on if configured. The live state comes from [Events-and-Live-State](Events-and-Live-State.md).

## When the model is slow

The model call has a timeout. On timeout the bot falls back to silence or, for events, to a canned line. It does not retry into the next turn. The gate has its own latency budget and fails closed (see [Safety-Model](Safety-Model.md)).

## Kill switch and dry run

A moderator command and a config flag stop the bot from posting at once. A dry-run mode runs the whole pipeline and logs what it would have said without sending it. Both exist so the first live run is not the first time anyone sees the output.
