# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""The action allowlist.

A model can request only actions the config names (say, tts, scene_change). Each action has
its own limits, and a stream-touching action is never reachable from untrusted chat text
alone. Seam only.
"""
