# Twitch bot account

Status: design. The Twitch adapter is being written in hypeman-social, and this page summarises its documentation rather than repeating it.

The bot is its own Twitch account and never the broadcaster's. A chat token can type in chat. If it is the broadcaster's, a leak lets an attacker speak as the broadcaster, with the broadcaster's moderation powers, on the channel that matters most. A separate account caps the damage at one muted, removable, replaceable user. It also lets the bot tell its own messages from the streamer's.

The step-by-step setup lives in the hypeman repository: [docs/TWITCH_BOT.md](https://github.com/ChiefGyk3D/hypeman/blob/main/docs/TWITCH_BOT.md). That file is the source of truth. The page may not be on the default branch yet, since it ships with the Twitch adapter work. This page only gives the shape.

## The shape

- A new account with its own email address, two-factor authentication on, and a name that says it is a bot.
- Its own Twitch application, a confidential client, not shared with another tool.
- The smallest scopes that work. The hypeman doc asks for `user:read:chat` to receive and `user:write:chat` to send, and says not to request more. `user:bot` and `channel:bot` matter for the Chat Bot Badge and the app-token path, which that adapter does not use. Scope names should be re-checked against Twitch's current documentation when the adapter ships.
- Moderator status only if a feature needs it, granted deliberately by the broadcaster. Moderation actions would be separate allowlist entries, off by default, and moderation is not LLMFAO's job anyway.
- Client secret and tokens live in Doppler. Nothing goes in the repository, a log, a crash report or the model's context.
- The token is validated on the schedule Twitch requires, and a failure raises an alert instead of retrying forever.
- The bot says it is a bot, in its profile and in chat when asked.

## Revoke and rotate

Stop the daemon. As the bot account, disconnect the application in Twitch's connections settings, which invalidates its tokens. Generate a new client secret in the developer console (register a new application if the client id leaked). Run the authorisation flow again as the bot, update the values in Doppler, and start the daemon again. The bot does not speak until its secrets validate. The hypeman doc has the full ordering.

Related: [Safety-Model](Safety-Model.md), [Deployment](Deployment.md).
