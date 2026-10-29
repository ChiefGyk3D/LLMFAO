# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""Strict, typed config loader.

Refused before any Python object is built: input over `MAX_CONFIG_BYTES`, invalid UTF-8,
more than one document, anchors, aliases, merge keys, explicit tags, nesting deeper than
`MAX_DEPTH`. Refused while building: duplicate keys and non-string keys. Refused on
validation: unknown keys at every level, wrong types, out-of-range values. Every failure is
a `ConfigError`; messages name keys, never values.

The config holds secret *names* (`SecretRef`), never values.
"""

from __future__ import annotations

import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml
from yaml.events import AliasEvent, CollectionStartEvent, ScalarEvent

from llmfao.secrets import SecretRef

MAX_CONFIG_BYTES = 64 * 1024
MAX_DEPTH = 8

PROVIDERS = ("ollama", "gemini", "openai", "claude")
ACTIONS = ("say", "tts", "scene_change")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}\Z")


class ConfigError(Exception):
    """The config is unreadable, hostile or invalid."""


# ---- safe parsing ----------------------------------------------------------


class _UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            if not isinstance(key_node, yaml.ScalarNode):
                raise ConfigError("mapping keys must be plain scalars")
            key = self.construct_object(key_node, deep=True)
            if not isinstance(key, str):
                raise ConfigError("mapping keys must be strings")
            if key in seen:
                raise ConfigError(f"duplicate key {key!r}")
            seen.add(key)
        return super().construct_mapping(node, deep)


def _scan_events(text: str) -> None:
    """Reject hostile structure from the event stream, before construction."""
    depth = 0
    docs = 0
    try:
        for ev in yaml.parse(text, Loader=yaml.SafeLoader):
            if isinstance(ev, yaml.DocumentStartEvent):
                docs += 1
                if docs > 1:
                    raise ConfigError("more than one YAML document")
            elif isinstance(ev, AliasEvent):
                raise ConfigError("YAML aliases are not allowed")
            if getattr(ev, "anchor", None) is not None:
                raise ConfigError("YAML anchors are not allowed")
            if getattr(ev, "tag", None) is not None:
                raise ConfigError("explicit YAML tags are not allowed")
            if isinstance(ev, CollectionStartEvent):
                depth += 1
                if depth > MAX_DEPTH:
                    raise ConfigError("YAML nested too deeply")
            elif isinstance(ev, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
                depth -= 1
            elif isinstance(ev, ScalarEvent) and ev.value == "<<" and ev.style is None:
                raise ConfigError("YAML merge keys are not allowed")
    except yaml.YAMLError:
        raise ConfigError("invalid YAML") from None


def parse_config(source: str | bytes) -> Config:
    """Parse and validate config text. Raises `ConfigError` for anything wrong."""
    raw = source.encode("utf-8") if isinstance(source, str) else source
    if len(raw) > MAX_CONFIG_BYTES:
        raise ConfigError("config too large")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ConfigError("config is not valid UTF-8") from None
    _scan_events(text)
    try:
        data = yaml.load(text, Loader=_UniqueKeyLoader)  # noqa: S506  # SafeLoader subclass
    except ConfigError:
        raise
    except (yaml.YAMLError, RecursionError, ValueError):
        raise ConfigError("invalid YAML") from None
    return _build(data)


def load_config(path: str | Path) -> Config:
    """Read at most `MAX_CONFIG_BYTES` from a regular file and parse it."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    except OSError:
        raise ConfigError("cannot open config file") from None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ConfigError("config path is not a regular file")
        with os.fdopen(fd, "rb", closefd=False) as fh:
            raw = fh.read(MAX_CONFIG_BYTES + 1)
    except OSError:
        raise ConfigError("cannot read config file") from None
    finally:
        os.close(fd)
    return parse_config(raw)


# ---- schema -----------------------------------------------------------------


def _section(value: Any, where: str, allowed: tuple[str, ...]) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{where}: expected a mapping")
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise ConfigError(f"{where}: unknown key(s): {', '.join(map(str, unknown))}")
    return value


def _str(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{where}: expected a non-empty string")
    return value


def _choice_list(value: Any, where: str, choices: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigError(f"{where}: expected a list")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or item not in choices:
            raise ConfigError(f"{where}: each entry must be one of {', '.join(choices)}")
        if item in out:
            raise ConfigError(f"{where}: duplicate entry")
        out.append(item)
    return tuple(out)


def _endpoint(value: Any, where: str) -> str:
    text = _str(value, where)
    parts = urlsplit(text)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ConfigError(f"{where}: expected an http(s) URL")
    if parts.username is not None or parts.password is not None:
        raise ConfigError(f"{where}: credentials do not belong in a URL")
    return text


@dataclass(frozen=True)
class BotConfig:
    name: str


@dataclass(frozen=True)
class ModelConfig:
    provider: str = "ollama"
    name: str = "gemma4:12b"
    endpoint: str | None = None
    fallback: tuple[str, ...] = ()


@dataclass(frozen=True)
class GateConfig:
    endpoint: str | None = None
    timeout_ms: int = 2000


@dataclass(frozen=True)
class ActionsConfig:
    allow: tuple[str, ...] = ()


@dataclass(frozen=True)
class Config:
    bot: BotConfig
    model: ModelConfig = field(default_factory=ModelConfig)
    gate: GateConfig = field(default_factory=GateConfig)
    actions: ActionsConfig = field(default_factory=ActionsConfig)
    secrets: Mapping[str, SecretRef] = field(default_factory=dict)

    def redacted(self) -> str:
        """Human-readable form: secret names only, endpoints masked."""

        def mask(v: str | None) -> str:
            return "<unset>" if v is None else "<redacted>"

        lines = [
            f"bot.name: {self.bot.name}",
            f"model.provider: {self.model.provider}",
            f"model.name: {self.model.name}",
            f"model.endpoint: {mask(self.model.endpoint)}",
            f"model.fallback: {', '.join(self.model.fallback) or '(none)'}",
            f"gate.endpoint: {mask(self.gate.endpoint)}",
            f"gate.timeout_ms: {self.gate.timeout_ms}",
            f"actions.allow: {', '.join(self.actions.allow) or '(none)'}",
        ]
        for name, ref in sorted(self.secrets.items()):
            lines.append(f"secrets.{name}: {ref} (value never held)")
        return "\n".join(lines)

    __str__ = redacted
    __repr__ = redacted


def _build(data: Any) -> Config:
    top = _section(data, "config", ("bot", "model", "gate", "actions", "secrets"))
    if "bot" not in top:
        raise ConfigError("bot: required")
    bot_d = _section(top["bot"], "bot", ("name",))
    if "name" not in bot_d:
        raise ConfigError("bot.name: required")
    bot = BotConfig(name=_str(bot_d["name"], "bot.name"))

    m = _section(top.get("model", {}), "model", ("provider", "name", "endpoint", "fallback"))
    provider = m.get("provider", "ollama")
    if provider not in PROVIDERS:
        raise ConfigError(f"model.provider: must be one of {', '.join(PROVIDERS)}")
    fallback = _choice_list(m.get("fallback", []), "model.fallback", PROVIDERS)
    if provider in fallback:
        raise ConfigError("model.fallback: must not repeat the primary provider")
    model = ModelConfig(
        provider=provider,
        name=_str(m.get("name", "gemma4:12b"), "model.name"),
        endpoint=_endpoint(m["endpoint"], "model.endpoint") if "endpoint" in m else None,
        fallback=fallback,
    )

    g = _section(top.get("gate", {}), "gate", ("endpoint", "timeout_ms"))
    timeout = g.get("timeout_ms", 2000)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 60_000:
        raise ConfigError("gate.timeout_ms: expected an integer from 1 to 60000")
    gate = GateConfig(
        endpoint=_endpoint(g["endpoint"], "gate.endpoint") if "endpoint" in g else None,
        timeout_ms=timeout,
    )

    a = _section(top.get("actions", {}), "actions", ("allow",))
    actions = ActionsConfig(allow=_choice_list(a.get("allow", []), "actions.allow", ACTIONS))

    s = top.get("secrets", {})
    if not isinstance(s, dict):
        raise ConfigError("secrets: expected a mapping")
    secrets: dict[str, SecretRef] = {}
    for name, body in s.items():
        if not _NAME.match(name):
            raise ConfigError("secrets: names must be letters, digits and underscores")
        where = f"secrets.{name}"
        ref = _section(body, where, ("platform", "key"))
        if "platform" not in ref or "key" not in ref:
            raise ConfigError(f"{where}: platform and key are required")
        secrets[name] = SecretRef(_str(ref["platform"], where), _str(ref["key"], where))

    return Config(bot=bot, model=model, gate=gate, actions=actions, secrets=secrets)
