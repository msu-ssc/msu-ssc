import datetime

import freezegun

from msu_ssc import ssc_log


def test_utc_filename_timestamp():
    with freezegun.freeze_time(
        "2025-01-02 03:45:56.123456-05:00",
        tz_offset=datetime.timedelta(seconds=-5 * 3600),  # -05:00, EST
    ):
        assert ssc_log.utc_filename_timestamp() == "2025-01-02T03_45_56.log"

        # TIMESPECS
        assert ssc_log.utc_filename_timestamp(timespec="auto") == "2025-01-02T03_45_56.123456.log"
        assert ssc_log.utc_filename_timestamp(timespec="hours") == "2025-01-02T03.log"
        assert ssc_log.utc_filename_timestamp(timespec="minutes") == "2025-01-02T03_45.log"
        assert ssc_log.utc_filename_timestamp(timespec="seconds") == "2025-01-02T03_45_56.log"
        assert ssc_log.utc_filename_timestamp(timespec="milliseconds") == "2025-01-02T03_45_56.123.log"
        assert ssc_log.utc_filename_timestamp(timespec="microseconds") == "2025-01-02T03_45_56.123456.log"

        # PREFIX
        assert ssc_log.utc_filename_timestamp(prefix="prefix") == "prefix_2025-01-02T03_45_56.log"

        # SUFFIX
        assert ssc_log.utc_filename_timestamp(suffix="suffix") == "2025-01-02T03_45_56_suffix.log"

        # EXTENSION
        assert ssc_log.utc_filename_timestamp(extension=".txt") == "2025-01-02T03_45_56.txt"
        assert ssc_log.utc_filename_timestamp(extension="txt") == "2025-01-02T03_45_56.txt"

        # PREFIX, SUFFIX, EXTENSION
        assert (
            ssc_log.utc_filename_timestamp(
                prefix="prefix",
                suffix="suffix",
                extension=".txt",
            )
            == "prefix_2025-01-02T03_45_56_suffix.txt"
        )
