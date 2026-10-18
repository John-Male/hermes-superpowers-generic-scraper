import pytest

from generic_scraper.retry import retry_with_backoff


def test_retry_succeeds_after_transient_failures():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("boom")
        return "ok"

    result = retry_with_backoff(flaky, attempts=3, retry_on=(ConnectionError,), sleep=lambda s: None)
    assert result == "ok"
    assert calls["n"] == 3


def test_retry_raises_after_exhausting_attempts():
    def always_fails():
        raise ConnectionError("boom")

    with pytest.raises(ConnectionError):
        retry_with_backoff(always_fails, attempts=3, retry_on=(ConnectionError,), sleep=lambda s: None)


def test_retry_does_not_catch_unlisted_exceptions():
    def raises_value_error():
        raise ValueError("not transient")

    with pytest.raises(ValueError):
        retry_with_backoff(raises_value_error, attempts=3, retry_on=(ConnectionError,), sleep=lambda s: None)


def test_retry_raises_value_error_for_zero_attempts():
    def never_called():
        raise AssertionError("fn should not be called when attempts <= 0")

    with pytest.raises(ValueError):
        retry_with_backoff(never_called, attempts=0, retry_on=(ConnectionError,), sleep=lambda s: None)


def test_retry_raises_value_error_for_negative_attempts():
    def never_called():
        raise AssertionError("fn should not be called when attempts <= 0")

    with pytest.raises(ValueError):
        retry_with_backoff(never_called, attempts=-1, retry_on=(ConnectionError,), sleep=lambda s: None)
