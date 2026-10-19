# FAQ

Status: design. Answers describe intent, and where something is not built it says so.

## Can I run it?

No. There is a repository baseline and a spec. The first runnable thing will be a Twitch bot.

## Why a separate Twitch account?

So a leaked token costs you one replaceable bot user and not your channel. Details on [Twitch-Bot-Account](Twitch-Bot-Account.md).

## Can the bot be tricked into posting something awful?

Someone will try. The defences are that chat is treated as data, the draft goes through a gate that fails closed, and the model can only request allowlisted actions. None of that is a promise of perfection, and the kill switch exists for the day it is not enough. See [Safety-Model](Safety-Model.md).

## Does it moderate my chat?

No. Moderation is a separate role with separate credentials.

## Does it remember my viewers?

Only viewers who linked their accounts, only short facts, for 30 days since their last activity, and unlinking deletes them. Planned, not built.

## Does it train on my chat?

No. Discord message content is never used as training data, and private messages are not sent to external models.

## Which models does it use?

Ollama with `gemma4:12b` by default. Gemini, OpenAI and Claude are opt-in. See [Architecture](Architecture.md).

## Why not just use an existing bot?

Existing ones are fine and some do part of this. This one is meant to be open source, self-hostable, and strict about what it will say and do. That is a preference, not a verdict on anyone else's product.

## Where do I report a security problem?

The repository's SECURITY.md has the process.
