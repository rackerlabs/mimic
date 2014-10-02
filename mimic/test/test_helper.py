
from unittest import TestCase

from datetime import datetime
from mimic.util.helper import current_time_in_utc, fmt


def no_total_seconds_in_26(td):
    """
    There's no timedelta.total_seconds in Python 2.6.
    """
    return td.seconds + (td.days * 24 * 3600)


class TimeFormatTests(TestCase):
    """
    Tests for formatting time.
    """

    def test_utc_time(self):
        """
        :obj:`current_time_in_utc` formats the current time as UTC.
        """
        close_to_now = datetime.utcnow()
        parsed = datetime.strptime(current_time_in_utc(), fmt)
        fudge_factor = 60
        # Asserting about real time is tricky, so let's just say that it took
        # less than a minute to get from the first function call to the second
        # one.
        delta = no_total_seconds_in_26(close_to_now - parsed)
        self.assertTrue(abs(delta) < fudge_factor,
                        str(delta) + " was greater than a minute")
