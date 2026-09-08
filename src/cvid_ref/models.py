from dataclasses import dataclass
from datetime import datetime, timezone


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _required(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class CommunicationGrant:
    grant_id: str
    sender: str
    recipient: str
    purpose: str
    channel: str
    audience: str
    expires_at: datetime
    policy_epoch: int
    max_attempts: int = 1
    nonce: str = "nonce:default"
    handle_id: str = "handle:default"
    direction: str = "inbound"
    effect: str = "communication"

    def __post_init__(self) -> None:
        for name in ("grant_id", "sender", "recipient", "purpose", "channel", "audience", "nonce", "handle_id", "direction", "effect"):
            _required(name, getattr(self, name))
        object.__setattr__(self, "expires_at", _utc(self.expires_at))
        if self.policy_epoch < 0:
            raise ValueError("policy_epoch must not be negative")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least one")


@dataclass(frozen=True)
class CandidateRequest:
    transaction_id: str
    authenticated_sender: str
    recipient: str
    purpose: str
    channel: str
    audience: str
    grant_id: str
    nonce: str = "nonce:default"
    handle_id: str = "handle:default"
    direction: str = "inbound"
    effect: str = "communication"

    def __post_init__(self) -> None:
        for name in ("transaction_id", "authenticated_sender", "recipient", "purpose", "channel", "audience", "grant_id", "nonce", "handle_id", "direction", "effect"):
            _required(name, getattr(self, name))
