# LLMFAO

Status: design. Nothing here runs yet, and every page says which parts are plans.

LLMFAO is a conversational bot engine for livestreams and communities: who the bot is, what it remembers, when it speaks, what it is allowed to do, and whether a message may go out at all. The README spells the name out as Large Language Model Fucking Around Online, and that is the last time this wiki does. The Twitch account and the Discord application are plain "LLMFAO" because platform listings are held to a higher standard than a private server.

The first release is a Twitch bot with its own account. Discord comes second, and Matrix users reach it through the bridge we already run. YouTube and Kick come after that.

## Read in this order

- [Architecture](Architecture.md): the pipeline, and why platform clients and model providers live in a different repository.
- [Safety-Model](Safety-Model.md): the gate, and what the bot is never allowed to do.
- [Twitch-Bot-Account](Twitch-Bot-Account.md): why the bot is not the streamer's account.
- [Events-and-Live-State](Events-and-Live-State.md): subs, raids, tips and knowing when you are live.
- [Queue-and-Rate-Limits](Queue-and-Rate-Limits.md): what happens when everything arrives at once.
- [Deployment](Deployment.md) and [Persona](Persona.md): both planned, both unbuilt.
- [Roadmap](Roadmap.md): MVP, next, later.
- [How-We-Build](How-We-Build.md) and [FAQ](FAQ.md).

## What exists today

A repository baseline: CI, security scanning, a spec, and this wiki. The code follows the plan. If a page describes a behaviour in the present tense, it describes the design, and the page header says so.

## This wiki is generated

Every page is a mirror of a file under `docs/wiki/` in the repository, rebuilt on each push to main. Edit the file, not the wiki.
