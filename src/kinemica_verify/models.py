"""Verification result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CheckGroup:
    """Result for one verification category."""

    name: str
    passed: bool
    failures: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "passed": self.passed,
            "failures": list(self.failures),
        }


@dataclass(frozen=True)
class VerificationReport:
    """Complete deterministic verification result."""

    groups: tuple[CheckGroup, ...]

    @property
    def verified(self) -> bool:
        return all(group.passed for group in self.groups)

    def to_dict(self) -> dict[str, object]:
        return {
            "verified": self.verified,
            "checks": [group.to_dict() for group in self.groups],
        }
