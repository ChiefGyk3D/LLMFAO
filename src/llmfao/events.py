# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""Neutral events: the one shape every platform event is converted to on the way in.

Holds the event record (id, source, kind, time, actor, amount, message and so on) and the
dedupe key `(platform, kind, source_id)`. Adapters in hypeman-social produce platform
payloads; this module owns the neutral form. Viewer text here is untrusted data. Seam only.
"""
