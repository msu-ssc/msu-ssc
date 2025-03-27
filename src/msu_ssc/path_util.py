import datetime
import re
import sys
from pathlib import Path
from typing import Union

if sys.version_info >= (3, 8):
    from typing import Literal

    TimespecType = Literal["auto", "hours", "minutes", "seconds", "milliseconds", "microseconds"]
else:
    TimespecType = str

_chunk_regex = re.compile(r"[^a-zA-Z0-9\-_\.]+")


def clean_path_part(part: str) -> str:
    return re.sub(_chunk_regex, "_", part)


def _is_valid_path_chunk(chunk: str) -> bool:
    return chunk == clean_path_part(chunk)


def clean_path(path: Path) -> Path:
    return Path(*(clean_path_part(part) for part in Path(path).parts))


def file_timestamp(
    timestamp: Union[datetime.datetime, None] = None,
    *,
    sep="T",
    timespec: TimespecType = "seconds",
    assume_utc=False,
    assume_local=False,
    desired_tz: Union[datetime.tzinfo, None] = None,
) -> str:
    """
    Convert a timestamp to a string suitable for use in a file name.

    Using all defaults will give you a string like `"2025-01-01T00_00_00"`, where the time is the current system time in UTC.

    TIME ZONES:
    - The `desired_tz` parameter is the time zone to which the timestamp will be converted before formatting. Default is UTC.
    - If the input is naive (i.e., has no time zone info), you must pass either `assume_utc=True` or `assume_local=True`. If
    you want something more complex, you'll need to convert the timestamp yourself before passing it in.

    Args:
        timestamp: The timestamp to convert. If None, the current time is used.
        sep: The separator between the date and time components.
        timespec: The level of precision to include in the time component.
        assume_utc: If True, assume the timestamp is in UTC.
        assume_local: If True, assume the timestamp is in the local time zone.
        desired_tz: The time zone to which the timestamp will be converted before formatting. Default is UTC.

    Returns:
        A string representation of the timestamp.
    """
    timestamp = timestamp or datetime.datetime.now(tz=datetime.timezone.utc)
    desired_tz = desired_tz or datetime.timezone.utc

    naive = timestamp.tzinfo is None
    if naive:
        if assume_utc and assume_local:
            raise ValueError("Cannot assume both UTC and local time")
        elif not assume_utc and not assume_local:
            raise ValueError("Must assume either UTC or local time if timestamp is naive")
        if assume_utc:
            timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)
        elif assume_local:
            timestamp = timestamp.astimezone(datetime.timezone.utc)

    assert timestamp.tzinfo is not None, "Timestamp must have time zone info"

    # This is weird: We need to convert to UTC, but then strip the time zone info
    # to avoid the "+00:00" in the string
    timestamp = timestamp.astimezone(desired_tz).replace(tzinfo=None)

    return clean_path_part(timestamp.isoformat(sep=sep, timespec=timespec))


if __name__ == "__main__":
    pass
    strings = [
        "",
        ".git",
        "2025-01-02T12:34:56.789012",
    ]

    for string in strings:
        print(f"string={string!r}")
        print(f"clean_path_part(string)={clean_path_part(string)!r}")
        print(f"_is_valid_path_chunk(string)={_is_valid_path_chunk(string)!r}")
        print()

    print(clean_path(Path("~/2025-01-02T12:34:56.789012.log")))

    class TZ(datetime.tzinfo):
        """A time zone with an arbitrary, constant -06:39 offset."""

        def utcoffset(self, dt):
            return datetime.timedelta(hours=+6, minutes=+39)

    dt = datetime.datetime(
        2025,
        1,
        2,
        12,
        00,
        00,
        0,
        # tzinfo=TZ(),
    )

    print(
        file_timestamp(
            dt,
            timespec="milliseconds",
            # assume_utc=True,
            assume_local=True,
        )
    )

    print(file_timestamp())
