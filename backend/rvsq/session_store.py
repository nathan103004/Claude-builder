import threading
import time
import uuid
from typing import Optional, TypedDict, Union

from models.rvsq_models import RAMQCredentials, RVSQError
from selenium_runner import get_driver


class _SessionEntry(TypedDict):
    driver: object
    credentials: RAMQCredentials
    created_at: float
    last_used_at: float


_store: dict[str, _SessionEntry] = {}
_lock = threading.Lock()
_TTL_SECONDS = 1800  # 30 minutes


def create_session(credentials: RAMQCredentials) -> str:
    session_id = str(uuid.uuid4())
    driver = get_driver()
    now = time.time()
    with _lock:
        _store[session_id] = {
            "driver": driver,
            "credentials": credentials,
            "created_at": now,
            "last_used_at": now,
        }
    return session_id


def get_session(session_id: str) -> Optional[_SessionEntry]:
    with _lock:
        return _store.get(session_id)


def touch_session(session_id: str) -> None:
    with _lock:
        if session_id in _store:
            _store[session_id]["last_used_at"] = time.time()


def delete_session(session_id: str) -> None:
    with _lock:
        entry = _store.pop(session_id, None)
    if entry:
        try:
            entry["driver"].quit()
        except Exception:
            pass


def is_session_valid(session_id: str, max_age_seconds: int = _TTL_SECONDS) -> bool:
    entry = get_session(session_id)
    if not entry:
        return False
    return (time.time() - entry["last_used_at"]) < max_age_seconds


def _get_login_rvsq():
    """Lazy import of login_rvsq to avoid circular imports at module load time."""
    from rvsq.login import login_rvsq  # noqa: PLC0415
    return login_rvsq


# Module-level reference — can be patched in tests via
# patch("rvsq.session_store.login_rvsq", ...)
def login_rvsq(driver, credentials):  # pragma: no cover
    return _get_login_rvsq()(driver, credentials)


def reauth_session(session_id: str) -> Union[bool, RVSQError]:
    entry = get_session(session_id)
    if not entry:
        return RVSQError(code="SESSION_EXPIRED", message="Session not found.")
    result = login_rvsq(entry["driver"], entry["credentials"])
    if isinstance(result, RVSQError):
        return result
    touch_session(session_id)
    return True


def delete_all_sessions() -> None:
    with _lock:
        ids = list(_store.keys())
    for sid in ids:
        delete_session(sid)
