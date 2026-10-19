# Persona

Status: planned. There is no persona loader yet, and this page describes what the file is meant to hold.

A persona is a file, not code, so changing the bot's character never means changing the engine. The plan for what goes in it:

- A system prompt: who the bot is and how it talks.
- Tone settings and a short list of things it must never say.
- Lore the bot may draw on, and an emote list for the channel.
- Per-feature instructions, so a raid thank-you and a chat answer can sound different.
- Permissions per feature: broadcaster only, moderators, VIPs, subscribers, everyone.

A persona does not hold secrets, and it cannot widen the action allowlist or loosen the gate. Those belong to config and the engine. The persona text sits in the model's instructions and chat text never does, which is why a viewer cannot rewrite it by typing.

Because the persona is identical every turn, providers that support prompt caching can reuse it. That is a hypeman-social concern and is also unbuilt.

See [Safety-Model](Safety-Model.md) for what a persona cannot override.
