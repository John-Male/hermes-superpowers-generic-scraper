"""Retry/backoff utility for transient failures."""
from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry_with_backoff(
    fn: Callable[[], T],
    attempts: int,
    retry_on: tuple[type[Exception], ...],
    base_delay: float = 0.01,
    multiplier: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``fn`` up to ``attempts`` times, retrying on exceptions in ``retry_on``.

    Between attempts, sleeps ``base_delay * multiplier ** attempt_index`` seconds
    (attempt_index starting at 0 for the delay after the first failed attempt).
    Re-raises the last exception if all attempts fail. Exceptions not listed in
    ``retry_on`` propagate immediately without retry.
    """
    last_exc: Exception | None = None
    if attempts <= 0:
        raise ValueError(f"attempts must be >= 1, got {attempts!r}")
    for attempt_index in range(attempts):
        try:
            return fn()
        except retry_on as exc:
            last_exc = exc
            if attempt_index < attempts - 1:
                sleep(base_delay * multiplier**attempt_index)
    assert last_exc is not None
    raise last_exc
