import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime


try:
    import rich
    from rich import logging as rich_logging

    _rich_available = True

except ImportError:
    _rich_available = False


def create_logger(
    name: str,
    parent: logging.Logger | None = None,
    level: str = "DEBUG",
    force_utc: bool = True,
    use_rich: bool = True,
) -> logging.Logger:
    if parent:
        logger = parent.getChild(suffix=name)
    else:
        logger = logging.getLogger(name=name)

    logger.setLevel(level=level)

    if use_rich and _rich_available:
        if force_utc:
            # Make a Custom function to convert the timestamp (which will be a naive `datetime` in the PC's timezone)
            # to a UTC string.
            #
            # This is necessary because RichHandler does not use the normal `logging.Formatter` machinery,
            # and has no built-in ability to create a UTC timestamp.
            #
            # NOTE: Timestamp ultimately displayed on screen is defined in `rich.logging.RichHandler.render` as:
            #
            # log_time = datetime.fromtimestamp(record.created)
            import datetime

            def _timestamp_converter(
                timestamp: "datetime.datetime", format_string="%X"
            ) -> str:
                return f"{timestamp.astimezone(datetime.timezone.utc):{format_string}}"
        else:

            def _timestamp_converter(
                timestamp: "datetime.datetime", format_string="%X"
            ) -> str:
                return f"{timestamp:{format_string}}"

        console_handler = rich_logging.RichHandler(
            omit_repeated_times=False,
            rich_tracebacks=True,
            log_time_format=_timestamp_converter,
        )

        # TODO: rich logging does not allow converting to UTC as of 13.9.4
        # .venv/lib/python3.10/site-packages/rich/logging.py
    else:
        # Create a StreamHandler and set the level
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        if force_utc:
            import time

            formatter.converter = time.gmtime
        console_handler.setFormatter(formatter)

    console_handler.setLevel(level=level)
    logger.addHandler(console_handler)

    return logger


ssc_root_logger = create_logger("ssc_root")

debug = ssc_root_logger.debug
info = ssc_root_logger.info
warning = ssc_root_logger.warning
error = ssc_root_logger.error
critical = ssc_root_logger.critical

if __name__ == "__main__":
    logger = create_logger(
        __file__,
        level="DEBUG",
        # force_utc=False,
        # use_rich=False,
    )
    logger.debug(f"This is a debug message.")
    logger.info(f"This is a info message.")
    logger.warning(f"This is a warning message.")
    logger.error(f"This is a error message.")
    logger.critical(f"This is a critical message.")
    try:
        1 / 0
    except Exception as exc:
        logger.error(
            f"This is an error message with exception info", exc_info=exc
        )
        # logger.error(f"This is an error message with extra", extra={"foo": "bar"})

    debug(f"DIRECT debug message.")
    info(f"DIRECT info message.")
    warning(f"DIRECT warning message.")
    error(f"DIRECT error message.")
    critical(f"DIRECT critical message.")
    try:
        1 / 0
    except Exception as exc:
        error(
            f"This is an error message with exception info", exc_info=exc
        )
