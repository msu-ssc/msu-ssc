import datetime
import logging
import sys
from pathlib import Path
from typing import Union

if sys.version_info >= (3, 8):
    from typing import Literal

    TimespecType = Literal["auto", "hours", "minutes", "seconds", "milliseconds", "microseconds"]
else:
    TimespecType = str

from msu_ssc.path_util import clean_path_part
from msu_ssc.path_util import file_timestamp

try:
    from rich.logging import RichHandler

    _rich_imported = True
except ImportError:
    _rich_imported = False

logger = logging.getLogger("ssc")
"""The primary logger. It will have the name `ssc`. Use `ssc_log.init()` to configure."""


def utc_filename_timestamp(
    timestamp: Union[datetime.datetime, None] = None,
    *,
    prefix: str = "",
    suffix: str = "",
    extension: str = ".log",
    timespec: TimespecType = "seconds",
    assume_utc=False,
    assume_local=False,
) -> str:
    """Generate a filename with a UTC timestamp.

    With all defaults, will give a filename like `2025-02-03T12_34_56.log`

    To make a `equipment_2025-02-03T12_34_56.789_log.txt`, you would call:

    ```
    filename = utc_filename_timestamp(
        prefix="equipment",
        suffix="log",
        extension=".txt",
        timespec="milliseconds",
    )
    ```
    """
    timestamp_string = file_timestamp(
        timestamp=timestamp,
        sep="T",
        timespec=timespec,
        desired_tz=datetime.timezone.utc,
        assume_utc=assume_utc,
        assume_local=assume_local,
    )
    if not extension.startswith("."):
        extension = "." + extension
    return clean_path_part("_".join(x for x in (prefix, timestamp_string, suffix) if x) + extension)


# logger.setLevel("DEBUG")

console_plain_text_formatter = logging.Formatter(
    fmt="[%(asctime)s.%(msecs)03d %(levelname)-8s] %(message)s",
    datefmt="%H:%M:%S",
)

plain_text_formatter = logging.Formatter(
    fmt="[%(asctime)s.%(msecs)03d %(levelname)-8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _iso_str(timestamp: "datetime.datetime") -> str:
    return f"{timestamp:%H:%M:%S.%f}"[:-3]


if _rich_imported:
    console_handler = RichHandler(
        level="DEBUG",
        show_time=True,
        omit_repeated_times=False,
        rich_tracebacks=True,
        # log_time_format="[%Y-%m-%d %H:%M:%S.%f]",
        log_time_format=_iso_str,
    )
else:
    console_handler = logging.StreamHandler()
    console_handler.setLevel("DEBUG")
    console_handler.setFormatter(console_plain_text_formatter)


def init(
    level: Union[str, None] = "INFO",
    *,
    plain_text_file_path: Union[Path, str, None] = None,
    jsonl_file_path: Union[Path, str, None] = None,
    plain_text_level: Union[str, None] = None,
    jsonl_level: Union[str, None] = None,
    console_level: Union[str, None] = None,
    console_: str = "%Y-%m-%d %H:%M:%S.%f",
) -> None:
    if level:
        logger.setLevel(level.upper())

    if plain_text_file_path:
        plain_text_level = plain_text_level or level
        _log_to_file(
            plain_text_file_path,
            level=plain_text_level,
        )

    if jsonl_file_path:
        jsonl_level = jsonl_level or level
        _log_to_jsonl_file(
            jsonl_file_path,
            level=jsonl_level,
        )

    console_level = console_level or level
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)


DEFAULT_LOG_DIRECTORY = Path(__file__).expanduser().resolve().parent.parent / "logs"
"""Should be `./logs/`"""


def log_to_default_file() -> None:
    """Begin logging to default file, which will be a timestamped file in ./logs/

    Name will be like `./logs/stk_2025-02-03T12_34_56.log`
    """
    import datetime

    file_name = f"stk_{datetime.datetime.now():%Y-%m-%dT%H_%M_%S}.log"
    file_path = DEFAULT_LOG_DIRECTORY / file_name
    _log_to_file(path=file_path)


def _log_to_file(
    path: Union[Path, str],
    level: Union[str, None] = None,
    *,
    encoding: str | None = "utf-8",
) -> None:
    """Begin logging in plaintext to the given file. File will be APPENDED, and encoded in UTF-8"""
    resolved_path = Path(path).expanduser().resolve()
    if not resolved_path.parent.exists():
        resolved_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    file_handler = logging.FileHandler(
        filename=Path(resolved_path).expanduser().resolve(),
        encoding=encoding,
    )

    if level:
        file_handler.setLevel(level)
    file_handler.setFormatter(plain_text_formatter)
    logger.addHandler(file_handler)
    logger.debug(f"Begin logging to {resolved_path.__fspath__()!r}")


def _log_to_jsonl_file(
    path: Union[Path, str],
    level: Union[str, None] = None,
) -> None:
    """Begin logging to the given file. File will be APPENDED, and encoded in UTF-8"""
    try:
        from pythonjsonlogger.jsonlogger import JsonFormatter
        # from pythonjsonlogger.json import JsonFormatter
    except ImportError:
        logger.error("pythonjsonlogger is not installed. Please install it to use JSON logging.")
        raise

    resolved_path = Path(path).expanduser().resolve()
    if not resolved_path.parent.exists():
        resolved_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
    file_handler = logging.FileHandler(filename=Path(resolved_path).expanduser().resolve())

    if level:
        file_handler.setLevel(level)
    json_formatter = JsonFormatter(
        reserved_attrs=(
            "msg",
            "args",
            "levelno",
        ),
    )
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    logger.debug(f"Begin logging to {resolved_path.__fspath__()!r}")


def getChild(name):
    return logger.getChild(name)


log = logger.log
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical


if __name__ == "__main__":
    # log_to_file(r"C:\Users\msu\Desktop\LEMS - InProgress\Analysis\logs\log.log")
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    init(
        level="DEBUG",
        # plain_text_file_path="logs/log.log",
        plain_text_file_path=f"logs/{utc_filename_timestamp(now, prefix=logger.name, extension='.log')}",
        jsonl_file_path=f"logs/{utc_filename_timestamp(now, prefix=logger.name, extension='.jsonl')}",
    )
    # log_to_default_file()

    debug("DEBUG MESSAGE")
    info("INFO MESSAGE")
    warning("WARNING MESSAGE")
    error("ERROR MESSAGE")
    critical("CRITICAL MESSAGE")

    # info("\n\nThis has\n\n\n\multiple newlines\n\n\n")

    # try:
    #     1 / 0
    # except Exception as exc:
    #     error("An error occurred", exc_info=exc)

    child = logger.getChild("child")

    child.info("Child info")
