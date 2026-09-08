from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from .models import CandidateRequest, CommunicationGrant


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    idempotent: bool = False


class InMemoryGrantState:
    """Atomic logical-act consumption for one process; replace in production."""
    def __init__(self) -> None:
        self._lock = Lock()
        self._current_epoch: dict[str, int] = {}
        self._consumed: dict[str, set[str]] = {}

    def set_epoch(self, recipient: str, epoch: int) -> None:
        if not recipient.strip():
            raise ValueError("recipient must be non-empty")
        if epoch < 0:
            raise ValueError("epoch must not be negative")
        with self._lock:
            self._current_epoch[recipient] = epoch

    def current_epoch(self, recipient: str) -> int | None:
        with self._lock:
            return self._current_epoch.get(recipient)

    def reserve(self, grant: CommunicationGrant, transaction_id: str) -> Decision:
        with self._lock:
            used = self._consumed.setdefault(grant.grant_id, set())
            if transaction_id in used:
                return Decision(True, "idempotent retransmission", True)
            if len(used) >= grant.max_attempts:
                return Decision(False, "attempt quota exhausted")
            used.add(transaction_id)
            return Decision(True, "authorized")


class EnforcementEngine:
    def __init__(self, state: InMemoryGrantState) -> None:
        self.state = state

    def evaluate(self, grant: CommunicationGrant | None, request: CandidateRequest, now: datetime | None = None) -> Decision:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("evaluation time must be timezone-aware")
        now = now.astimezone(timezone.utc)
        if grant is None or grant.grant_id != request.grant_id:
            return Decision(False, "unknown grant")
        if grant.expires_at <= now:
            return Decision(False, "grant expired")
        current_epoch = self.state.current_epoch(grant.recipient)
        if current_epoch is None:
            return Decision(False, "no authoritative policy epoch")
        if grant.policy_epoch != current_epoch:
            return Decision(False, "grant policy epoch is stale or revoked")
        fields = (("sender", grant.sender, request.authenticated_sender), ("recipient", grant.recipient, request.recipient),
                  ("purpose", grant.purpose, request.purpose), ("channel", grant.channel, request.channel),
                  ("audience", grant.audience, request.audience), ("nonce", grant.nonce, request.nonce),
                  ("handle", grant.handle_id, request.handle_id), ("direction", grant.direction, request.direction),
                  ("effect", grant.effect, request.effect))
        for name, expected, actual in fields:
            if expected != actual:
                return Decision(False, f"{name} mismatch")
        return self.state.reserve(grant, request.transaction_id)
