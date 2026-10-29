# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""The turn pipeline: filter, context, model, gate, action.

Orders the stages of one turn and owns nothing else. Each stage is a seam filled in by a later
issue; the gate stage is mandatory and a draft never skips it. Seam only.
"""
