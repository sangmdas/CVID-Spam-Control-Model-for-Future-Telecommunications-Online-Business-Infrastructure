import hashlib
import hmac
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime

from .models import CommunicationGrant


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=lambda x: x.isoformat() if isinstance(x, datetime) else str(x)).encode()


@dataclass(frozen=True)
class GrantEnvelope:
    grant: CommunicationGrant
    issuer: str
    key_id: str
    signature: str = ""

    def unsigned(self): return {"grant": asdict(self.grant), "issuer": self.issuer, "key_id": self.key_id}


class HMACAuthenticator:
    """Dependency-free integrity adapter. Replace with managed asymmetric keys where required."""
    def __init__(self, key: bytes):
        if len(key) < 32: raise ValueError("key must be at least 32 bytes")
        self._key = key

    def sign_envelope(self, envelope: GrantEnvelope) -> GrantEnvelope:
        sig = hmac.new(self._key, canonical(envelope.unsigned()), hashlib.sha256).hexdigest()
        return replace(envelope, signature=sig)

    def verify_envelope(self, envelope: GrantEnvelope) -> bool:
        expected = hmac.new(self._key, canonical(envelope.unsigned()), hashlib.sha256).hexdigest()
        return bool(envelope.signature) and hmac.compare_digest(expected, envelope.signature)

    def sign_dict(self, value: dict) -> str: return hmac.new(self._key, canonical(value), hashlib.sha256).hexdigest()
    def verify_dict(self, value: dict, signature: str) -> bool: return bool(signature) and hmac.compare_digest(self.sign_dict(value), signature)
