# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""The outbound queue and the single sender.

Four classes (events, mentions, commands, ambient), each with its own limit, lifetime and
full-queue policy, drained by one sender bounded by cooldowns. In memory; a restart does not
replay it. Seam only.
"""
