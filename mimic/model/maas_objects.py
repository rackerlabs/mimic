"""
MaaS API data model
"""

import random
import time


def random_letters(len_min, len_max=None):
    """
    Makes a string with random letters (a-z).
    """
    if len_max is None:
        len_max = len_min
    return ''.join([chr(ord('a') + random.randint(0, 25))
                    for _ in xrange(random.randint(len_min, len_max))])


class TestCheckMetric(object):
    """
    Models a metric from the test-check API
    """
    def __init__(self, name, type, unit='other'):
        """
        Constructs a test check metric data source
        """
        self.name = name
        self.type = type
        self._unit = unit
        self._override = None

    def set_override(self, value):
        """
        Sets the override metric value.

        We wrap the override value in a dict so that we can distinguish
        between None (i.e., null) and no override.
        """
        self._override = {'value': value}

    def clear_override(self):
        """
        Clears the override metric value.
        """
        self._override = None

    def _get_default_data(self):
        """
        Gets the default data point. This data point may be overridden by
        setting the override value.
        """
        if self.type == 'i':
            return random.randint(0, 100000)
        elif self.type == 'n':
            if self._unit == 'percent':
                return random.uniform(0, 100)
            else:
                return random.uniform(0, 100000)
        elif self.type == 's':
            return random_letters(12, 30)
        raise ValueError('No default data getter for type {0}!'.format(self.type))

    def get_value(self):
        """
        Gets the metric data object as returned from the test-check API.
        """
        data = (self._get_default_data() if self._override is None
                else self._override['value'])
        return {'type': self.type,
                'unit': self._unit,
                'data': data}


class TestCheckData(object):
    """
    Models test-check response data
    """
    def __init__(self, metrics):
        """
        Initializes the test-check responder
        """
        self.metrics = metrics
        self.available = True
        self.status = "code=200,rt=0.4s,bytes=99"
        self.response_code = 200

    def get_metric_by_name(self, metric_name):
        """
        Gets the metric on this test-check.

        This method is useful for setting and clearing overrides on the
        test metrics.
        """
        for metric in self.metrics:
            if metric.name == metric_name:
                return metric
        raise NameError('No metric named "{0}"!'.format(metric_name))

    def get_response(self):
        """
        Gets the test-check response.
        """
        monitoring_zone = random_letters(6)
        return (self.response_code,
                [{'timestamp': int(time.time() * 1000),
                  'monitoring_zone_id': monitoring_zone,
                  'available': self.available,
                  'status': self.status,
                  'metrics': dict([(m.name, m.get_value()) for m in self.metrics])}])


test_check_responses = {}

test_check_responses['agent.cpu'] = lambda: TestCheckData([
    TestCheckMetric('user_percent_average', 'n', 'percent'),
    TestCheckMetric('wait_percent_average', 'n', 'percent'),
    TestCheckMetric('sys_percent_average', 'n', 'percent'),
    TestCheckMetric('idle_percent_average', 'n', 'percent'),
    TestCheckMetric('irq_percent_average', 'n', 'percent'),
    TestCheckMetric('usage_average', 'n', 'percent'),
    TestCheckMetric('min_cpu_usage', 'n', 'percent'),
    TestCheckMetric('max_cpu_usage', 'n', 'percent'),
    TestCheckMetric('stolen_percent_average', 'n', 'percent')])

test_check_responses['agent.disk'] = lambda: TestCheckData([
    TestCheckMetric('queue', 'i'),
    TestCheckMetric('read_bytes', 'i', 'bytes'),
    TestCheckMetric('reads', 'i', 'count'),
    TestCheckMetric('rtime', 'i'),
    TestCheckMetric('wtime', 'i'),
    TestCheckMetric('write_bytes', 'i', 'bytes'),
    TestCheckMetric('writes', 'i', 'count')])

test_check_responses['agent.filesystem'] = lambda: TestCheckData([
    TestCheckMetric('avail', 'i', 'kilobytes'),
    TestCheckMetric('free', 'i', 'kilobytes'),
    TestCheckMetric('options', 's', 'string'),
    TestCheckMetric('total', 'i', 'kilobytes'),
    TestCheckMetric('used', 'i', 'kilobytes'),
    TestCheckMetric('files', 'i', 'count'),
    TestCheckMetric('free_files', 'i', 'count')])

test_check_responses['agent.load_average'] = lambda: TestCheckData([
    TestCheckMetric('1m', 'n'),
    TestCheckMetric('5m', 'n'),
    TestCheckMetric('10m', 'n')])

test_check_responses['agent.memory'] = lambda: TestCheckData([
    TestCheckMetric('actual_free', 'i', 'bytes'),
    TestCheckMetric('actual_used', 'i', 'bytes'),
    TestCheckMetric('free', 'i', 'bytes'),
    TestCheckMetric('ram', 'i', 'megabytes'),
    TestCheckMetric('swap_free', 'i', 'bytes'),
    TestCheckMetric('swap_page_in', 'i', 'bytes'),
    TestCheckMetric('swap_page_out', 'i', 'bytes'),
    TestCheckMetric('swap_total', 'i', 'bytes'),
    TestCheckMetric('swap_used', 'i', 'bytes'),
    TestCheckMetric('total', 'i', 'bytes'),
    TestCheckMetric('used', 'i', 'bytes')])

test_check_responses['agent.network'] = lambda: TestCheckData([
    TestCheckMetric('rx_bytes', 'i', 'bytes'),
    TestCheckMetric('rx_dropped', 'i', 'bytes'),
    TestCheckMetric('rx_errors', 'i', 'bytes'),
    TestCheckMetric('rx_packets', 'i', 'bytes'),
    TestCheckMetric('tx_bytes', 'i', 'bytes'),
    TestCheckMetric('tx_dropped', 'i', 'bytes'),
    TestCheckMetric('tx_errors', 'i', 'bytes'),
    TestCheckMetric('tx_packets', 'i', 'bytes')])

test_check_responses['remote.http'] = lambda: TestCheckData([
    TestCheckMetric('rx_bytes', 'i', 'bytes'),
    TestCheckMetric('rx_dropped', 'i', 'bytes'),
    TestCheckMetric('rx_errors', 'i', 'bytes'),
    TestCheckMetric('rx_packets', 'i', 'bytes'),
    TestCheckMetric('tx_bytes', 'i', 'bytes'),
    TestCheckMetric('tx_dropped', 'i', 'bytes'),
    TestCheckMetric('tx_errors', 'i', 'bytes'),
    TestCheckMetric('tx_packets', 'i', 'bytes')])

test_check_responses['remote.ping'] = lambda: TestCheckData([
    TestCheckMetric('available', 'n', 'percent'),
    TestCheckMetric('average', 'n'),
    TestCheckMetric('count', 'i', 'count'),
    TestCheckMetric('maximum', 'n'),
    TestCheckMetric('minimum', 'n')])


def get_test_check_response_by_type(check_type):
    """
    Looks up the correct test-check data response by check type.

    This should not be used if a test-check responder exists for the
    desired entity ID and check type. The responder should be cached
    so that the metric values can be overridden.
    """
    return test_check_responses[check_type]()
