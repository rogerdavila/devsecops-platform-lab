from datetime import datetime, timezone
from threading import Lock

_lock = Lock()
_started: bool = False
_draining: bool = False
_start_time: datetime = datetime.now(timezone.utc)


def startup_complete() -> None:
    global _started
    with _lock:
        _started = True


def begin_drain() -> None:
    global _draining
    with _lock:
        _draining = True


def is_ready() -> bool:
    with _lock:
        return _started and not _draining


def is_alive() -> bool:
    return True


def get_start_time() -> datetime:
    return _start_time


def reset() -> None:
    global _started, _draining, _start_time
    with _lock:
        _started = False
        _draining = False
        _start_time = datetime.now(timezone.utc)
