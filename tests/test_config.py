# SPDX-FileCopyrightText: Copyright (C) 2026 ChiefGyk3D
# SPDX-License-Identifier: GPL-3.0-or-later
"""The config loader: strict schema, hostile YAML refused, secrets by name only."""

from __future__ import annotations

import logging
import os
import pickle
import threading
from pathlib import Path
from typing import BinaryIO

import pytest

from llmfao.config import MAX_CONFIG_BYTES, Config, ConfigError, load_config, parse_config
from llmfao.secrets import SecretError, SecretRef, SecretValue, resolve_secret

VALID = """\
bot:
  name: TestBot
model:
  provider: ollama
  name: gemma4:12b
  endpoint: http://ollama.example.invalid:11434
  fallback: [gemini]
gate:
  endpoint: http://guard.example.invalid:11434
  timeout_ms: 1500
actions:
  allow: [say, tts]
secrets:
  chat_token:
    platform: Twitch
    key: access_token
"""


def test_valid_config_loads() -> None:
    cfg = parse_config(VALID)
    assert isinstance(cfg, Config)
    assert cfg.bot.name == "TestBot"
    assert cfg.model.name == "gemma4:12b"
    assert cfg.model.fallback == ("gemini",)
    assert cfg.gate.timeout_ms == 1500
    assert cfg.actions.allow == ("say", "tts")
    assert cfg.secrets["chat_token"] == SecretRef(platform="Twitch", key="access_token")


def test_defaults_are_safe() -> None:
    cfg = parse_config("bot:\n  name: TestBot\n")
    assert cfg.model.provider == "ollama"
    assert cfg.model.name == "gemma4:12b"
    assert cfg.model.fallback == ()  # fallback is opt-in
    assert cfg.actions.allow == ()  # allowlist, empty by default
    assert cfg.secrets == {}


def test_load_from_path(tmp_path: Path) -> None:
    p = tmp_path / "c.yaml"
    p.write_text(VALID, encoding="utf-8")
    assert load_config(p).bot.name == "TestBot"


def test_missing_file_is_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(tmp_path / "nope.yaml")


def test_directory_is_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(tmp_path)


@pytest.mark.parametrize(
    ("text", "why"),
    [
        ("bot:\n  name: A\n  name: B\n", "duplicate key"),
        ("bot:\n  name: A\nbot:\n  name: B\n", "duplicate key"),
        ("x: &a {name: A}\nbot: *a\n", "anchors"),
        ("bot: &a\n  name: A\n", "anchors"),
        ("base: &b {name: A}\nbot:\n  <<: *b\n", "anchors"),
        ("bot:\n  <<: {name: A}\n", "merge keys"),
        ("bot:\n  name: A\n---\nbot:\n  name: B\n", "more than one"),
        ("bot:\n  name: !!str A\n", "explicit YAML tags"),
        ("bot: !!python/object/apply:os.system ['true']\n", "explicit YAML tags"),
        ("bot: [unclosed\n", "invalid YAML"),
        ("- a\n- b\n", "expected a mapping"),
        ("", "expected a mapping"),
        ("bot: " + "[" * 200 + "]" * 200 + "\n", "nested too deeply"),
        ("bot:\n  name: [" * 1 + "[" * 20 + "]" * 20 + "]\n", "nested too deeply"),
        ("1: x\nbot:\n  name: A\n", "keys must be strings"),
    ],
)
def test_hostile_yaml_is_refused(text: str, why: str) -> None:
    with pytest.raises(ConfigError, match=why):
        parse_config(text)


def test_malformed_deep_nesting_is_config_error() -> None:
    with pytest.raises(ConfigError):
        parse_config("bot:\n  name: " + "[" * 200 + "\n")


def test_oversized_input_refused_without_parsing() -> None:
    big = "bot:\n  name: " + "a" * (MAX_CONFIG_BYTES + 1) + "\n"
    with pytest.raises(ConfigError, match="too large"):
        parse_config(big)


def test_oversized_file_reads_at_most_cap_plus_one(tmp_path: Path) -> None:
    p = tmp_path / "big.yaml"
    p.write_bytes(b"#" * (MAX_CONFIG_BYTES * 3))
    with pytest.raises(ConfigError, match="too large"):
        load_config(p)


class _SpyReader:
    def __init__(self, inner: BinaryIO, sizes: list[int]) -> None:
        self._inner = inner
        self._sizes = sizes

    def __enter__(self) -> _SpyReader:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def read(self, n: int = -1) -> bytes:
        self._sizes.append(n)
        return self._inner.read(n)


def test_file_read_is_bounded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sizes: list[int] = []

    def spy(fd: int, mode: str, closefd: bool = True) -> _SpyReader:
        return _SpyReader(open(fd, "rb", closefd=closefd), sizes)

    p = tmp_path / "big.yaml"
    p.write_bytes(b"#" * (MAX_CONFIG_BYTES * 3))
    monkeypatch.setattr("llmfao.config.os.fdopen", spy)
    with pytest.raises(ConfigError):
        load_config(p)
    assert sizes == [MAX_CONFIG_BYTES + 1]


def test_symlink_is_refused(tmp_path: Path) -> None:
    real = tmp_path / "real.yaml"
    real.write_text(VALID, encoding="utf-8")
    link = tmp_path / "link.yaml"
    link.symlink_to(real)
    with pytest.raises(ConfigError):
        load_config(link)


def test_fifo_is_refused(tmp_path: Path) -> None:
    fifo = tmp_path / "f.yaml"
    os.mkfifo(fifo)
    # Hold a reader open so a non-blocking writer can attach and supply VALID config:
    # only the S_ISREG check can then refuse the path.
    rfd = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    wfd = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
    try:
        os.write(wfd, VALID.encode())
        outcome: list[object] = []

        def run() -> None:
            try:
                outcome.append(load_config(fifo))
            except ConfigError as e:
                outcome.append(e)

        t = threading.Thread(target=run, daemon=True)
        t.start()
        t.join(timeout=5)
        assert not t.is_alive(), "load_config blocked on a FIFO"
    finally:
        os.close(wfd)
        os.close(rfd)
    assert len(outcome) == 1
    err = outcome[0]
    assert isinstance(err, ConfigError)
    assert "not a regular file" in str(err)


def test_fifo_without_a_writer_does_not_block(tmp_path: Path) -> None:
    fifo = tmp_path / "f.yaml"
    os.mkfifo(fifo)
    outcome: list[BaseException | None] = []

    def run() -> None:
        try:
            load_config(fifo)
            outcome.append(None)
        except ConfigError as e:
            outcome.append(e)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout=3)
    if t.is_alive():
        # Release the stuck blocking open so the thread can finish.
        wfd = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
        os.close(wfd)
        t.join(timeout=3)
        pytest.fail("load_config blocked opening a FIFO with no writer")
    assert isinstance(outcome[0], ConfigError)


def test_symlinked_parent_directory_is_followed(tmp_path: Path) -> None:
    # Documented trust boundary: the caller owns trust of the path; only the final
    # component is symlink-checked. Changing this must be a deliberate decision.
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "c.yaml").write_text(VALID, encoding="utf-8")
    (tmp_path / "linkdir").symlink_to(real_dir, target_is_directory=True)
    assert isinstance(load_config(tmp_path / "linkdir" / "c.yaml"), Config)


def test_invalid_utf8_is_config_error() -> None:
    with pytest.raises(ConfigError):
        parse_config(b"bot:\n  name: \xff\xfe\n")


@pytest.mark.parametrize(
    "text",
    [
        "bot:\n  name: A\n  extra: 1\n",  # unknown nested key
        "bot:\n  name: A\nsurprise: 1\n",  # unknown top-level key
        "bot:\n  name: A\nmodel:\n  nmae: x\n",
        "bot:\n  name: A\ngate:\n  timeout: 5\n",
        "bot:\n  name: A\nactions:\n  allow: [say]\n  deny: []\n",
        "bot:\n  name: A\nsecrets:\n  s:\n    platform: P\n    key: k\n    value: hunter2\n",
    ],
)
def test_unknown_keys_rejected(text: str) -> None:
    with pytest.raises(ConfigError, match="unknown"):
        parse_config(text)


@pytest.mark.parametrize(
    "text",
    [
        "{}\n",  # bot is required
        "bot: {}\n",  # name is required
        "bot: {name: ''}\n",
        "bot: {name: 5}\n",
        "bot: {name: true}\n",
        "bot: just-a-string\n",
        "bot: {name: A}\nmodel: {provider: carrierpigeon}\n",
        "bot: {name: A}\nmodel: {fallback: [nope]}\n",
        "bot: {name: A}\nmodel: {fallback: gemini}\n",
        "bot: {name: A}\nmodel: {provider: ollama, fallback: [ollama]}\n",
        "bot: {name: A}\ngate: {timeout_ms: 0}\n",
        "bot: {name: A}\ngate: {timeout_ms: 600000}\n",
        "bot: {name: A}\ngate: {timeout_ms: true}\n",
        "bot: {name: A}\ngate: {timeout_ms: '5'}\n",
        "bot: {name: A}\nactions: {allow: [launch_missiles]}\n",
        "bot: {name: A}\nactions: {allow: [say, say]}\n",
        "bot: {name: A}\nsecrets: {s: {platform: P}}\n",
        "bot: {name: A}\nsecrets: {s: plain-text-secret}\n",
        "bot: {name: A}\nsecrets: {'bad name': {platform: P, key: k}}\n",
        "bot: {name: A}\nmodel: {endpoint: 'file:///etc/passwd'}\n",
        "bot: {name: A}\nmodel: {endpoint: 'http://user:pw@host.invalid'}\n",
    ],
)
def test_invalid_values_rejected(text: str) -> None:
    with pytest.raises(ConfigError):
        parse_config(text)


def test_errors_never_echo_values() -> None:
    with pytest.raises(ConfigError) as exc:
        parse_config("bot: {name: A}\nsecrets: {s: SUPERSECRETVALUE}\n")
    assert "SUPERSECRETVALUE" not in str(exc.value)


def test_redacted_output_hides_endpoints_and_has_secret_names_only() -> None:
    cfg = parse_config(VALID)
    text = cfg.redacted()
    assert "TestBot" in text
    assert "chat_token" in text  # the name is fine
    assert "ollama.example.invalid" not in text
    assert "guard.example.invalid" not in text
    assert text == str(cfg)
    assert text == repr(cfg)


# ---- secrets -------------------------------------------------------------

SENTINEL = "s3cr3t-VALUE-0xDEADBEEF"


def test_secret_value_is_redacted_everywhere_but_reveal() -> None:
    v = SecretValue(SENTINEL)
    assert SENTINEL not in repr(v)
    assert SENTINEL not in str(v)
    assert SENTINEL not in f"{v}"
    assert SENTINEL not in f"{v!r:>40}"
    assert v.reveal() == SENTINEL


def test_resolve_uses_the_getter_by_platform_and_key() -> None:
    seen: list[tuple[str, str]] = []

    def getter(platform: str, key: str) -> str | None:
        seen.append((platform, key))
        return SENTINEL

    v = resolve_secret(SecretRef("Twitch", "access_token"), getter=getter)
    assert seen == [("Twitch", "access_token")]
    assert v.reveal() == SENTINEL


def test_secret_value_never_reaches_a_log_line(caplog: pytest.LogCaptureFixture) -> None:
    ref = SecretRef("Twitch", "access_token")
    with caplog.at_level(logging.DEBUG):
        v = resolve_secret(ref, getter=lambda _p, _k: SENTINEL)
        logging.getLogger("llmfao").info("have %s and %r", v, v)
        # Even logging the whole loaded config cannot leak: it holds names only.
        cfg = parse_config(VALID)
        logging.getLogger("llmfao").info("config %s %r", cfg, cfg)
        # A failed resolve logs the name, not a value.
        with pytest.raises(SecretError):
            resolve_secret(ref, getter=lambda _p, _k: None)
    assert caplog.records, "the guard must have collected something"
    assert SENTINEL not in caplog.text
    assert (
        "Twitch" in caplog.text
    )  # negative control: the name is logged, so the check can see text


def test_guard_bites_when_a_value_is_logged_raw(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        logging.getLogger("llmfao").info("oops %s", SecretValue(SENTINEL).reveal())
    assert SENTINEL in caplog.text


def test_missing_secret_is_an_error_naming_the_ref_only() -> None:
    with pytest.raises(SecretError) as exc:
        resolve_secret(SecretRef("Twitch", "access_token"), getter=lambda _p, _k: None)
    assert "Twitch" in str(exc.value)


def test_empty_secret_is_missing() -> None:
    with pytest.raises(SecretError):
        resolve_secret(SecretRef("Twitch", "access_token"), getter=lambda _p, _k: "")


def test_getter_exception_does_not_leak_its_text() -> None:
    def getter(_p: str, _k: str) -> str | None:
        raise RuntimeError(f"backend said {SENTINEL}")

    with pytest.raises(SecretError) as exc:
        resolve_secret(SecretRef("Twitch", "access_token"), getter=getter)
    assert SENTINEL not in str(exc.value)
    assert exc.value.__context__ is None
    assert exc.value.__cause__ is None


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_secret_value_cannot_be_pickled(protocol: int) -> None:
    with pytest.raises(TypeError) as exc:
        pickle.dumps(SecretValue(SENTINEL), protocol=protocol)
    assert SENTINEL not in str(exc.value)
    assert SENTINEL not in repr(exc.value)


def test_default_getter_is_hypemans_get_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TWITCH_ACCESS_TOKEN", SENTINEL)
    monkeypatch.delenv("DOPPLER_TOKEN", raising=False)
    monkeypatch.setenv("SECRETS_MANAGER", "none")
    assert resolve_secret(SecretRef("Twitch", "access_token")).reveal() == SENTINEL
