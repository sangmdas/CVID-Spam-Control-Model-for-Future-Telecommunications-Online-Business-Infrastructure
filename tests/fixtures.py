from datetime import datetime, timedelta, timezone

from cvid_ref import CandidateRequest, CommunicationGrant, EnforcementEngine, InMemoryGrantState


NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


def setup(max_attempts=1, epoch=7):
    state = InMemoryGrantState()
    state.set_epoch("user:U", epoch)
    engine = EnforcementEngine(state)
    grant = CommunicationGrant("g-1", "business:B", "user:U", "enquiry:42", "voice", "sbc:west", NOW + timedelta(minutes=5), epoch, max_attempts)
    return state, engine, grant


def request(**changes):
    fields = dict(transaction_id="sip-call-1", authenticated_sender="business:B", recipient="user:U", purpose="enquiry:42", channel="voice", audience="sbc:west", grant_id="g-1")
    fields.update(changes)
    return CandidateRequest(**fields)
