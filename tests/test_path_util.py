import datetime

from msu_ssc import ssc_log

timestamp_utc = datetime.datetime(2025, 1, 2, 3, 45, 56, 123456, tzinfo=datetime.timezone.utc)
timestamp_naive = datetime.datetime(2025, 1, 2, 3, 45, 56, 123456)


def test_file_timestamp():
    assert ssc_log.file_timestamp(timestamp=timestamp_utc) == "2025-01-02T03_45_56"

    # TIMESPECS
    assert ssc_log.file_timestamp(timestamp=timestamp_utc, timespec="auto") == "2025-01-02T03_45_56.123456"
    assert ssc_log.file_timestamp(timestamp=timestamp_utc, timespec="hours") == "2025-01-02T03"
    assert ssc_log.file_timestamp(timestamp=timestamp_utc, timespec="minutes") == "2025-01-02T03_45"
    assert ssc_log.file_timestamp(timestamp=timestamp_utc, timespec="seconds") == "2025-01-02T03_45_56"
    assert ssc_log.file_timestamp(timestamp=timestamp_utc, timespec="milliseconds") == "2025-01-02T03_45_56.123"
    assert ssc_log.file_timestamp(timestamp=timestamp_utc, timespec="microseconds") == "2025-01-02T03_45_56.123456"

    # ASSUME_UTC
    assert ssc_log.file_timestamp(timestamp=timestamp_naive, assume_utc=True) == "2025-01-02T03_45_56"

    # ASSUME_LOCAL
    # My word, this is annoying.
    # timestamp_naive = datetime.datetime(2025, 1, 15)

    # Get _tzinfo.   https://stackoverflow.com/a/39079819
    local_timezone: datetime.timezone = timestamp_naive.astimezone().tzinfo
    utcoffset = local_timezone.utcoffset(timestamp_naive)
    simple_timestamp_naive_plus_offset = timestamp_naive - utcoffset
    manually_converted_to_utc = simple_timestamp_naive_plus_offset.replace(tzinfo=datetime.timezone.utc)
    automatically_converted_to_utc = timestamp_naive.astimezone(datetime.timezone.utc)

    assert manually_converted_to_utc == automatically_converted_to_utc
    assert ssc_log.file_timestamp(timestamp=timestamp_naive, assume_local=True) == ssc_log.file_timestamp(
        timestamp=manually_converted_to_utc,
    )


def test_utc_filename_timestamp():
    import datetime

    assert ssc_log.utc_filename_timestamp(timestamp=timestamp_utc) == "2025-01-02T03_45_56.log"

    assert datetime
    pass


if __name__ == "__main__":
    # pytest.main([__file__])
    pass
