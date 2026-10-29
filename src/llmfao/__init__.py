# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""LLMFAO: an AI-powered, multi-platform interaction engine.

Module layout (`src/llmfao`). Platform and provider code lives in hypeman-social, not here.

- `llmfao.config`: typed, strict YAML config loader; unknown keys, duplicate keys, aliases,
  merge keys and oversized input are refused; prints redacted.
- `llmfao.secrets`: secrets referenced by name and resolved through hypeman-social's secrets
  layer; a resolved value never prints.
- `llmfao.events`: the neutral event record.
- `llmfao.pipeline`: filter, context, model, gate, action for one turn.
- `llmfao.queue`: the outbound queue and the single sender.
- `llmfao.gate`: the safety gate; fails closed.
- `llmfao.actions`: the action allowlist.
- `llmfao.persona`: the fixed persona and rules block.

Use hypeman-social's `is_available()` for provider availability, never the `enabled` attribute.
"""

__version__ = "0.0.0"
