# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""The safety gate every outbound message passes before it is sent.

Deterministic rules first, then a classifier on a separate instance. It fails closed: an
unreachable guard, a timeout or an unparseable verdict means the message is dropped. Seam only.
"""
