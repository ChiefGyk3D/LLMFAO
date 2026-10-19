# Deployment

Status: planned. Nothing in this page is built, and there is no image to pull.

The intended shapes, in the order they are likely to happen:

- A Docker image, so the engine runs the same everywhere.
- On-prem, next to the Ollama server the model calls go to.
- Cloud, where the engine runs hosted and reaches an on-prem Ollama through a Twingate ZTNA connector instead of an open port. The cloud side never gets a route into the home network, only to the one service it needs.
- Secrets from Doppler in every case. The repository holds names only, CI uses its own config over OIDC, and runtime secrets live in a separate runtime project, never in the CI one.

Open questions are the cloud provider, how the classifier instance for the gate is placed relative to the main model, and what the container runs as. They get answered when there is something to run.

See [Twitch-Bot-Account](Twitch-Bot-Account.md) for the one credential setup that has to happen by hand.
