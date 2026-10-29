# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""Secrets by name only, resolved through hypeman-social's secrets layer.

The repository and the loaded config hold a `SecretRef` (platform and key). The value exists
only inside a `SecretValue`, which prints as a placeholder; `reveal()` is the one way out and
call sites should pass the result straight to the client that needs it.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

log = logging.getLogger(__name__)

SecretGetter = Callable[[str, str], str | None]


class SecretError(Exception):
    """A secret could not be resolved. The message names the reference, never a value."""


@dataclass(frozen=True)
class SecretRef:
    """Where a secret lives: a platform bundle and a key. Never the value."""

    platform: str
    key: str

    def __str__(self) -> str:
        return f"{self.platform}.{self.key}"


class SecretValue:
    """A resolved secret that refuses to print itself."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "SecretValue(<redacted>)"

    __str__ = __repr__

    def __format__(self, spec: str) -> str:
        return format(repr(self), spec)

    def __reduce__(self) -> str:
        raise TypeError("SecretValue is not picklable")


def _hypeman_getter(platform: str, key: str) -> str | None:
    # Imported lazily: hypeman-social's secrets layer reads Doppler, the environment, etc.
    from hypeman_social.config.secrets import get_secret

    return get_secret(platform, key)


def resolve_secret(ref: SecretRef, getter: SecretGetter | None = None) -> SecretValue:
    """Resolve `ref` through `getter` (default: hypeman-social's `get_secret`)."""
    fetch = getter or _hypeman_getter
    failed = False
    value: str | None = None
    try:
        value = fetch(ref.platform, ref.key)
    except Exception:
        failed = True
    if failed:
        # Raised outside the except block so the backend exception (whose text could
        # carry a value) is neither __cause__ nor __context__; report the reference only.
        log.warning("secret %s: lookup failed", ref)
        raise SecretError(f"secret {ref}: lookup failed")
    if not value:
        log.warning("secret %s: not found", ref)
        raise SecretError(f"secret {ref}: not found")
    log.debug("secret %s: resolved", ref)
    return SecretValue(value)
