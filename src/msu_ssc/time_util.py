import datetime


def utc() -> datetime.datetime:
    """Get the current system time, in UTC, as a timezone-aware `datetime` object.

    Note that this is not the same as `datetime.utcnow()`, whish returns a naive `datetime`
    object, and is deprecated as of Python 3.12. See https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow

    Returns:
        datetime.datetime: A timezone-aware datetime object
    """
    return datetime.datetime.now(tz=datetime.timezone.utc)
