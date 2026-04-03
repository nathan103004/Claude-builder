import threading
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

from models.rvsq_models import RAMQCredentials


def _creds():
    return RAMQCredentials(
        prenom="Marie", nom="Tremblay",
        numero_assurance_maladie="TREM 1234 5678",
        numero_sequentiel="01",
        date_naissance_jour="15",
        date_naissance_mois="03",
        date_naissance_annee="1985",
    )


@pytest.fixture(autouse=True)
def clear_store():
    import rvsq.session_store as ss
    ss._store.clear()
    yield
    for sid in list(ss._store.keys()):
        ss.delete_session(sid)


def test_create_session_returns_uuid():
    from rvsq import session_store as ss
    with patch("rvsq.session_store.get_driver", return_value=MagicMock()):
        sid = ss.create_session(_creds())
    assert uuid.UUID(sid)  # raises if not valid UUID


def test_get_session_returns_none_for_missing():
    from rvsq import session_store as ss
    assert ss.get_session("nonexistent") is None


def test_get_session_returns_entry_for_valid_key():
    from rvsq import session_store as ss
    mock_driver = MagicMock()
    with patch("rvsq.session_store.get_driver", return_value=mock_driver):
        sid = ss.create_session(_creds())
    entry = ss.get_session(sid)
    assert entry is not None
    assert entry["driver"] is mock_driver


def test_delete_session_calls_driver_quit():
    from rvsq import session_store as ss
    mock_driver = MagicMock()
    with patch("rvsq.session_store.get_driver", return_value=mock_driver):
        sid = ss.create_session(_creds())
    ss.delete_session(sid)
    mock_driver.quit.assert_called_once()


def test_delete_session_noop_on_missing():
    from rvsq import session_store as ss
    ss.delete_session("does-not-exist")  # must not raise


def test_is_session_valid_true_within_ttl():
    from rvsq import session_store as ss
    with freeze_time("2026-04-03 10:00:00"):
        with patch("rvsq.session_store.get_driver", return_value=MagicMock()):
            sid = ss.create_session(_creds())
    with freeze_time("2026-04-03 10:29:00"):
        assert ss.is_session_valid(sid) is True


def test_is_session_valid_false_after_ttl():
    from rvsq import session_store as ss
    with freeze_time("2026-04-03 10:00:00"):
        with patch("rvsq.session_store.get_driver", return_value=MagicMock()):
            sid = ss.create_session(_creds())
    with freeze_time("2026-04-03 10:31:00"):
        assert ss.is_session_valid(sid) is False


def test_touch_session_updates_last_used():
    from rvsq import session_store as ss
    with freeze_time("2026-04-03 10:00:00"):
        with patch("rvsq.session_store.get_driver", return_value=MagicMock()):
            sid = ss.create_session(_creds())
    with freeze_time("2026-04-03 10:20:00"):
        ss.touch_session(sid)
    entry = ss.get_session(sid)
    assert entry["last_used_at"] == pytest.approx(
        time.mktime(time.strptime("2026-04-03 10:20:00", "%Y-%m-%d %H:%M:%S")), abs=2
    )


def test_reauth_calls_login_rvsq():
    from rvsq import session_store as ss
    with patch("rvsq.session_store.get_driver", return_value=MagicMock()):
        sid = ss.create_session(_creds())
    with patch("rvsq.session_store.login_rvsq", return_value=None) as mock_login:
        result = ss.reauth_session(sid)
    assert result is True
    mock_login.assert_called_once()


def test_concurrent_access_does_not_raise():
    from rvsq import session_store as ss
    errors = []
    def reader():
        try:
            ss.get_session("any-key")
        except Exception as e:
            errors.append(e)
    threads = [threading.Thread(target=reader) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
