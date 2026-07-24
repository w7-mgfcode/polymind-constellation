"""Closed, fail-closed capability vocabulary."""

from __future__ import annotations

from collections.abc import Iterable

from polymind.model import AtomicCapability, Capability

_ATOMIC = {item.value: item for item in AtomicCapability}
_COMPOUND: dict[str, frozenset[AtomicCapability]] = {
    "filesystem": frozenset({AtomicCapability.FILESYSTEM_READ, AtomicCapability.FILESYSTEM_WRITE}),
    "shell": frozenset({AtomicCapability.SHELL_READONLY, AtomicCapability.SHELL_EXECUTE}),
    "network": frozenset({AtomicCapability.NETWORK_READ, AtomicCapability.NETWORK_WRITE}),
    "browser": frozenset({AtomicCapability.BROWSER_READ, AtomicCapability.BROWSER_WRITE}),
}


def normalize_capability(declaration: str) -> Capability:
    """Expand one known declaration or reject it without guessing."""
    if declaration in _ATOMIC:
        return Capability(declaration, frozenset({_ATOMIC[declaration]}))
    if declaration in _COMPOUND:
        return Capability(declaration, _COMPOUND[declaration])
    raise ValueError(f"unknown capability: {declaration}")


def normalize_capabilities(declarations: Iterable[str]) -> tuple[Capability, ...]:
    """Normalize declarations deterministically and reject duplicates."""
    normalized: list[Capability] = []
    seen: set[str] = set()
    for declaration in declarations:
        if declaration in seen:
            raise ValueError(f"duplicate capability: {declaration}")
        seen.add(declaration)
        normalized.append(normalize_capability(declaration))
    return tuple(sorted(normalized, key=lambda item: item.declaration))
