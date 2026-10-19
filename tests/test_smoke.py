# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import llmfao


def test_package_has_a_version() -> None:
    assert llmfao.__version__.count(".") == 2
