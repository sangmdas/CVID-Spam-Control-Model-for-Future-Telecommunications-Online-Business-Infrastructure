from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from itertools import count
from threading import Lock

from .crypto import GrantEnvelope, HMACAuthenticator
from .engine import Decision, EnforcementEngine
from .models import CandidateRequest


@dataclass(frozen=True)
class ReleaseCapability:
    capability_id: str
    grant_id: str
    transaction_id: str
    sender: str
    audience: str
    resource_id: str
    effect: str
    expires_at: datetime
    signature: str = ""

    def unsigned(self):
        value = asdict(self); value.pop("signature", None); return value


@dataclass(frozen=True)
class FinalityDecision:
    allowed: bool
    reason: str
    capability: ReleaseCapability | None = None
    idempotent: bool = False


class FinalityEngine:
    def __init__(self, core: EnforcementEngine, authenticator: HMACAuthenticator, trusted_issuers: set[str], audience: str):
        self.core = core; self.authenticator = authenticator; self.trusted_issuers = set(trusted_issuers); self.audience = audience; self._ids = count(1)

    def evaluate(self, envelope: GrantEnvelope | None, request: CandidateRequest, now=None) -> FinalityDecision:
        now = now or datetime.now(timezone.utc)
        if envelope is None: return FinalityDecision(False, "grant envelope required")
        if envelope.issuer not in self.trusted_issuers: return FinalityDecision(False, "untrusted issuer")
        if not self.authenticator.verify_envelope(envelope): return FinalityDecision(False, "grant integrity invalid")
        result = self.core.evaluate(envelope.grant, request, now)
        if not result.allowed: return FinalityDecision(False, result.reason, idempotent=result.idempotent)
        capability = ReleaseCapability(f"release-{next(self._ids)}", envelope.grant.grant_id, request.transaction_id,
            request.authenticated_sender, self.audience, f"{request.channel}:{request.transaction_id}", request.effect,
            min(envelope.grant.expires_at, now + timedelta(seconds=5)))
        capability = replace(capability, signature=self.authenticator.sign_dict(capability.unsigned()))
        return FinalityDecision(True, result.reason, capability, result.idempotent)


class FinalityAllocator:
    """Simulated first point that can create the governed communication effect."""
    def __init__(self, authenticator: HMACAuthenticator, audience: str):
        self.authenticator = authenticator; self.audience = audience; self.effects: dict[str, str] = {}; self._lock = Lock()

    def allocate(self, capability: ReleaseCapability | None, sender: str, resource_id: str, now=None) -> Decision:
        now = now or datetime.now(timezone.utc)
        if capability is None: return Decision(False, "release capability required")
        if now.tzinfo is None: raise ValueError("allocation time must be timezone-aware")
        if not self.authenticator.verify_dict(capability.unsigned(), capability.signature): return Decision(False, "release integrity invalid")
        if now >= capability.expires_at: return Decision(False, "release capability expired")
        if capability.audience != self.audience: return Decision(False, "release audience mismatch")
        if capability.sender != sender: return Decision(False, "release sender mismatch")
        if capability.resource_id != resource_id: return Decision(False, "release resource mismatch")
        with self._lock:
            previous = self.effects.get(capability.transaction_id)
            if previous is not None and previous != resource_id: return Decision(False, "transaction resource conflict")
            self.effects[capability.transaction_id] = resource_id
        return Decision(True, "resource allocated", previous is not None)
