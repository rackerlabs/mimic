
from unittest import TestCase

from datetime import datetime
from mimic.util.helper import current_time_in_utc, fmt


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
        delta = (close_to_now - parsed).total_seconds()
        self.assertTrue(abs(delta) < fudge_factor,
                        str(delta) + " was greater than a minute")
