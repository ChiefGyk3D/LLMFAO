# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""Neutral events: the one shape every platform event is converted to on the way in.

Holds the event record (id, source, kind, time, actor, amount, message and so on) and the
dedupe key `(platform, kind, source_id)`. Adapters in hypeman-social produce platform
payloads (chat arrives as hypeman-social's `ChatEvent`, converted by `from_chat_event`);
this module owns the neutral form.

Viewer text is untrusted data. Names and messages are sanitised on construction (NFKC,
control, bidi, zero-width and other invisible characters removed, whitespace collapsed),
length-capped, and typed `UntrustedText` so a consumer can tell them from engine strings.
Ids are sanitised too, so a dedupe key cannot be spoofed with invisible characters.

`Deduper` drops repeats inside a ten minute window; `collapse_gifts` and `EventIntake`
fold a community gift together with its per-recipient children.
"""

from __future__ import annotations

import enum
import re
import time as _time
import unicodedata
from collections import OrderedDict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from hypeman_social.social.events import ChatEvent

DEDUPE_TTL_SECONDS = 600.0
DEDUPE_MAX_ENTRIES = 10_000
MAX_NAME_CHARS = 64
MAX_MESSAGE_CHARS = 500
MAX_ID_CHARS = 128
MAX_MONTHS = 1200
_RAW_SLACK = 4  # inspect at most cap * 4 raw characters; NFKC rarely expands more than 2x

#: Unicode categories removed outright: control, format (bidi, zero width, BOM), surrogate,
#: private use, unassigned. Line and paragraph separators become spaces.
_STRIP = frozenset({"Cc", "Cf", "Cs", "Co", "Cn"})
_SPACE_CATS = frozenset({"Zs", "Zl", "Zp"})
_WS = re.compile(r"\s+")
_TIERS = frozenset({"prime", "1000", "2000", "3000"})
_CURRENCY = re.compile(r"[A-Za-z0-9]{1,8}")


class EventError(ValueError):
    """An event field is invalid. The one error type this module raises."""


class UntrustedText(str):
    """Text that came from a viewer. Data, never instructions."""

    def __repr__(self) -> str:
        return f"UntrustedText({str.__repr__(self)})"


def sanitize_text(raw: str, max_chars: int) -> str:
    """Normalise, strip invisible and control characters, collapse spaces, cap the length."""
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    text = unicodedata.normalize("NFKC", raw[: max_chars * _RAW_SLACK])
    kept: list[str] = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat in _STRIP:
            if ch in "\t\n\r\x0b\x0c\x85":  # whitespace controls separate words
                kept.append(" ")
            continue
        kept.append(" " if cat in _SPACE_CATS else ch)
    out = _WS.sub(" ", "".join(kept)).strip()
    out = out[:max_chars].rstrip()
    return out


class EventKind(enum.StrEnum):
    CHAT = "chat"
    SUB = "sub"
    RESUB = "resub"
    SUB_GIFT = "sub_gift"  # one gifted sub, one recipient
    COMMUNITY_GIFT = "community_gift"  # a batch announcement; amount is the gift count
    CHEER = "cheer"
    RAID = "raid"
    TIP = "tip"
    FOLLOW = "follow"


def _clean_id(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise EventError(f"{label} must be a string")
    out = sanitize_text(value, MAX_ID_CHARS)
    if not out:
        raise EventError(f"{label} is empty")
    return out


def _untrusted(value: str | None, cap: int) -> UntrustedText | None:
    if value is None:
        return None
    return UntrustedText(sanitize_text(str(value), cap))


@dataclass(frozen=True)
class Event:
    """One event from any source. Frozen; fields are validated and sanitised on construction."""

    #: Fields holding viewer-controlled text. Consumers wrap these as data in every prompt.
    UNTRUSTED_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"actor_name", "message", "recipient_name"}
    )

    platform: str
    kind: EventKind
    source_id: str
    time: datetime
    actor_id: str
    actor_name: UntrustedText | None = None
    anonymous: bool = False
    amount: Decimal | None = None
    currency: str | None = None
    tier: str | None = None
    months: int | None = None
    message: UntrustedText | None = None
    recipient_id: str | None = None
    recipient_name: UntrustedText | None = None
    gift_batch_id: str | None = None

    def __post_init__(self) -> None:
        def put(name: str, value: object) -> None:
            object.__setattr__(self, name, value)

        put("platform", _clean_id(self.platform, "platform").lower())
        try:
            put("kind", EventKind(self.kind))
        except ValueError:
            raise EventError(f"unknown event kind {self.kind!r}") from None
        put("source_id", _clean_id(self.source_id, "source_id"))
        put("actor_id", _clean_id(self.actor_id, "actor_id"))
        if self.recipient_id is not None:
            put("recipient_id", _clean_id(self.recipient_id, "recipient_id"))
        if self.gift_batch_id is not None:
            put("gift_batch_id", _clean_id(self.gift_batch_id, "gift_batch_id"))
        if not isinstance(self.time, datetime) or self.time.utcoffset() is None:
            raise EventError("time must be a timezone-aware datetime")
        put("time", self.time.astimezone(UTC))
        put("actor_name", _untrusted(self.actor_name, MAX_NAME_CHARS))
        put("recipient_name", _untrusted(self.recipient_name, MAX_NAME_CHARS))
        put("message", _untrusted(self.message, MAX_MESSAGE_CHARS))
        if self.amount is not None and (
            not isinstance(self.amount, Decimal) or not self.amount.is_finite() or self.amount < 0
        ):
            raise EventError("amount must be a finite, non-negative Decimal")
        if self.currency is not None and not _CURRENCY.fullmatch(self.currency):
            raise EventError("currency must be 1-8 letters or digits")
        if self.tier is not None and self.tier not in _TIERS:
            raise EventError(f"unknown tier {self.tier!r}")
        if self.months is not None and (
            isinstance(self.months, bool)
            or not isinstance(self.months, int)
            or not 0 <= self.months <= MAX_MONTHS
        ):
            raise EventError(f"months must be an integer from 0 to {MAX_MONTHS}")

    @property
    def key(self) -> tuple[str, EventKind, str]:
        """The dedupe key."""
        return (self.platform, self.kind, self.source_id)


def from_chat_event(chat: ChatEvent, *, time: datetime | None = None) -> Event:
    """Convert hypeman-social's `ChatEvent`. Roles, bridge and self flags stay with the caller."""
    return Event(
        platform=chat.platform,
        kind=EventKind.CHAT,
        source_id=chat.message_id,
        time=time if time is not None else datetime.now(UTC),
        actor_id=chat.author_id,
        actor_name=UntrustedText(chat.author_name),
        message=UntrustedText(chat.text),
    )


class Deduper:
    """Remembers keys for `ttl` seconds. A repeat is a duplicate while its age is below `ttl`;
    at exactly `ttl` it is new again. A duplicate does not extend the window. The cache holds at
    most `max_size` keys; past that the oldest is forgotten (memory wins over perfect dedupe).
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float] = _time.monotonic,
        ttl: float = DEDUPE_TTL_SECONDS,
        max_size: int = DEDUPE_MAX_ENTRIES,
    ) -> None:
        if not ttl > 0:
            raise ValueError("ttl must be positive")
        if max_size < 1:
            raise ValueError("max_size must be at least 1")
        self._clock = clock
        self._ttl = ttl
        self._max = max_size
        self._seen: OrderedDict[tuple[str, EventKind, str], float] = OrderedDict()

    def __len__(self) -> int:
        return len(self._seen)

    def _purge(self, now: float) -> None:
        while self._seen:
            oldest = next(iter(self._seen.values()))
            if now - oldest < self._ttl:
                break
            self._seen.popitem(last=False)

    def admit(self, event: Event) -> bool:
        """True if the event is new (and is now remembered); False for a duplicate."""
        now = self._clock()
        self._purge(now)
        key = event.key
        if key in self._seen:
            return False
        self._seen[key] = now
        while len(self._seen) > self._max:
            self._seen.popitem(last=False)
        return True


def collapse_gifts(events: Iterable[Event]) -> list[Event]:
    """Drop each per-recipient gift whose community gift is in the same sequence.

    A gift child is matched to its parent by `(platform, gift_batch_id)`, in either order.
    Everything else is kept, in order.
    """
    items = list(events)
    batches = {
        (e.platform, e.gift_batch_id)
        for e in items
        if e.kind is EventKind.COMMUNITY_GIFT and e.gift_batch_id is not None
    }
    return [
        e
        for e in items
        if not (e.kind is EventKind.SUB_GIFT and (e.platform, e.gift_batch_id) in batches)
    ]


class EventIntake:
    """Streaming front door: drop duplicates, then absorb gift children of a seen community gift.

    A child that arrives before its parent cannot be recalled and is passed on; use
    `collapse_gifts` on a buffered batch when order is not guaranteed.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float] = _time.monotonic,
        ttl: float = DEDUPE_TTL_SECONDS,
        max_size: int = DEDUPE_MAX_ENTRIES,
    ) -> None:
        self._clock = clock
        self._ttl = ttl
        self._max = max_size
        self._dedupe = Deduper(clock=clock, ttl=ttl, max_size=max_size)
        self._batches: OrderedDict[tuple[str, str], float] = OrderedDict()

    @property
    def size(self) -> int:
        return len(self._dedupe) + len(self._batches)

    def accept(self, event: Event) -> Event | None:
        """The event to announce, or None if it is a duplicate or folded into a parent."""
        if not self._dedupe.admit(event):
            return None
        now = self._clock()
        while self._batches and now - next(iter(self._batches.values())) >= self._ttl:
            self._batches.popitem(last=False)
        if event.gift_batch_id is not None:
            batch = (event.platform, event.gift_batch_id)
            if event.kind is EventKind.COMMUNITY_GIFT:
                self._batches[batch] = now
                while len(self._batches) > self._max:
                    self._batches.popitem(last=False)
            elif event.kind is EventKind.SUB_GIFT and batch in self._batches:
                return None
        return event
