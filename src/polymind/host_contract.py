"""Fail-closed capability guidance for provider-neutral hosts."""

from __future__ import annotations

from dataclasses import dataclass

from polymind.model import AtomicCapability, PermissionMode


@dataclass(frozen=True, slots=True)
class HostPermission:
    """One capability's conservative generic-host permission requirement."""

    action: str
    mode: PermissionMode
    host_permissions: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "mode": self.mode.value,
            "host_permissions": list(self.host_permissions),
            "reason": self.reason,
        }


_MAPPINGS: dict[AtomicCapability, tuple[PermissionMode, tuple[str, ...], str]] = {
    AtomicCapability.FILESYSTEM_READ: (
        PermissionMode.ASK,
        ("read", "glob", "grep"),
        "constrain reads to validated workspace and package roots",
    ),
    AtomicCapability.FILESYSTEM_WRITE: (
        PermissionMode.ASK,
        ("edit",),
        "require an approved diff and writable-root boundary",
    ),
    AtomicCapability.SHELL_READONLY: (
        PermissionMode.ASK,
        ("bash",),
        "shell syntax cannot be assumed read-only across hosts",
    ),
    AtomicCapability.SHELL_EXECUTE: (
        PermissionMode.ASK,
        ("bash",),
        "require sandbox, limits, approval, and audit logging",
    ),
    AtomicCapability.NETWORK_READ: (
        PermissionMode.ASK,
        ("webfetch", "websearch"),
        "restrict destinations and prevent credential forwarding",
    ),
    AtomicCapability.NETWORK_WRITE: (
        PermissionMode.DENY,
        (),
        "generic hosts cannot safely represent arbitrary network mutation",
    ),
    AtomicCapability.BROWSER_READ: (
        PermissionMode.DENY,
        (),
        "no provider-neutral browser sandbox is defined",
    ),
    AtomicCapability.BROWSER_WRITE: (
        PermissionMode.DENY,
        (),
        "stateful browser actions require a provider-specific approval model",
    ),
    AtomicCapability.SECRET_ACCESS: (
        PermissionMode.DENY,
        (),
        "secrets are excluded from the generic host contract",
    ),
}


def map_host_permission(action: str) -> HostPermission:
    """Map one atomic capability or deny an unknown value without guessing."""
    try:
        atomic = AtomicCapability(action)
    except ValueError:
        return HostPermission(
            action,
            PermissionMode.DENY,
            (),
            "unknown capability has no validated host mapping",
        )
    mode, permissions, reason = _MAPPINGS[atomic]
    return HostPermission(atomic.value, mode, permissions, reason)


def map_host_permissions(actions: set[str] | frozenset[str]) -> tuple[HostPermission, ...]:
    """Return stable requirements for a set of atomic action strings."""
    return tuple(map_host_permission(action) for action in sorted(actions))
