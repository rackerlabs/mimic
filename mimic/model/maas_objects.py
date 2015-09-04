"""
MaaS API data model
"""

import random


def random_letters(len_min, len_max):
    """
    Makes a string with random letters (a-z).
    """
    return ''.join([chr(ord('a') + random.randint(0, 25))
                    for _ in xrange(random.randint(len_min, len_max))])


class Metric(object):
    """
    Models a MaaS metric type.
    """
    def __init__(self, name, type, clock, unit='other'):
        """
        Initializes the metric.
        """
        self.name = name
        self.type = type
        self._unit = unit
        self._overrides = {}
        self._clock = clock

    def _override_key(self, **kwargs):
        """
        Computes a key used for hashing overrides, as a tuple of strings.
        """
        return (kwargs['entity_id'],
                kwargs['check_id'],
                kwargs.get('monitoring_zone', '__AGENT__'))

    def set_override(self, **kwargs):
        """
        Sets the override metric for a given tenant, entity and check.

        Override metrics are defined as a function which takes a timestamp
        and returns the metric value.
        """
        self._overrides[self._override_key(**kwargs)] = kwargs['override_fn']

    def clear_overrides(self):
        """
        Clears the override metric values.
        """
        self._overrides = {}

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

    def get_value_for_test_check(self, **kwargs):
        """
        Gets the metric data object as returned from the test-check API.
        """
        override_key = self._override_key(**kwargs)
        timestamp = kwargs['timestamp']
        data = self._get_default_data()

        if override_key in self._overrides:
            data_fn = self._overrides[override_key]
            data = data_fn(timestamp)

        return {'type': self.type,
                'unit': self._unit,
                'data': data}


class CheckType(object):
    """
    Data model for a MaaS check type (e.g., remote.ping).
    """
    def __init__(self, clock, metrics):
        """
        Constructs a check type with metrics.
        """
        self.metrics = metrics
        self.test_check_available = {}
        self.test_check_status = {}
        self.test_check_response_code = {}
        self._clock = clock

    def clear_overrides(self):
        """
        Clears the overrides for test-checks and metrics.
        """
        self.test_check_available = {}
        self.test_check_status = {}
        self.test_check_response_code = {}

        for metric in self.metrics:
            metric.clear_overrides()

    def get_metric_by_name(self, metric_name):
        """
        Gets the metric on this check type.

        This method is useful for setting and clearing overrides on the
        test metrics.
        """
        for metric in self.metrics:
            if metric.name == metric_name:
                return metric
        raise NameError('No metric named "{0}"!'.format(metric_name))

    def get_test_check_response(self, **kwargs):
        """
        Gets the response as would have been returned by the test-check API.
        """
        entity_id = kwargs['entity_id']
        check_id = kwargs.get('check_id', '__test_check')
        monitoring_zones = kwargs.get('monitoring_zones') or ['__AGENT__']

        ench_key = (entity_id, check_id)
        timestamp = int(1000 * self._clock.seconds())

        return (self.test_check_response_code.get(ench_key, 200),
                [{'timestamp': timestamp,
                  'monitoring_zone_id': monitoring_zone,
                  'available': self.test_check_available.get(ench_key, True),
                  'status': self.test_check_status.get(
                      ench_key, 'code=200,rt=0.4s,bytes=99'),
                  'metrics': dict([(m.name,
                                    m.get_value_for_test_check(
                                        entity_id=entity_id,
                                        check_id=check_id,
                                        monitoring_zone=monitoring_zone,
                                        timestamp=timestamp))
                                   for m in self.metrics])}
                 for monitoring_zone in monitoring_zones])


class MaasStore(object):
    """
    A collection of MaaS configuration objects.
    """
    def __init__(self, clock):
        """
        Initializes the Maas configuration using the provided clock.
        """
        self.check_types = {
            'agent.cpu': CheckType(clock, [
                Metric('user_percent_average', 'n', clock, unit='percent'),
                Metric('wait_percent_average', 'n', clock, unit='percent'),
                Metric('sys_percent_average', 'n', clock, unit='percent'),
                Metric('idle_percent_average', 'n', clock, unit='percent'),
                Metric('irq_percent_average', 'n', clock, unit='percent'),
                Metric('usage_average', 'n', clock, unit='percent'),
                Metric('min_cpu_usage', 'n', clock, unit='percent'),
                Metric('max_cpu_usage', 'n', clock, unit='percent'),
                Metric('stolen_percent_average', 'n', clock, unit='percent')]),
            'agent.disk': CheckType(clock, [
                Metric('queue', 'i', clock),
                Metric('read_bytes', 'i', clock, unit='bytes'),
                Metric('reads', 'i', clock, unit='count'),
                Metric('rtime', 'i', clock),
                Metric('wtime', 'i', clock),
                Metric('write_bytes', 'i', clock, unit='bytes'),
                Metric('writes', 'i', clock, unit='count')]),
            'agent.filesystem': CheckType(clock, [
                Metric('avail', 'i', clock, unit='kilobytes'),
                Metric('free', 'i', clock, unit='kilobytes'),
                Metric('options', 's', clock, unit='string'),
                Metric('total', 'i', clock, unit='kilobytes'),
                Metric('used', 'i', clock, unit='kilobytes'),
                Metric('files', 'i', clock, unit='count'),
                Metric('free_files', 'i', clock, unit='count')]),
            'agent.load_average': CheckType(clock, [
                Metric('1m', 'n', clock),
                Metric('5m', 'n', clock),
                Metric('10m', 'n', clock)]),
            'agent.memory': CheckType(clock, [
                Metric('actual_free', 'i', clock, unit='bytes'),
                Metric('actual_used', 'i', clock, unit='bytes'),
                Metric('free', 'i', clock, unit='bytes'),
                Metric('ram', 'i', clock, unit='megabytes'),
                Metric('swap_free', 'i', clock, unit='bytes'),
                Metric('swap_page_in', 'i', clock, unit='bytes'),
                Metric('swap_page_out', 'i', clock, unit='bytes'),
                Metric('swap_total', 'i', clock, unit='bytes'),
                Metric('swap_used', 'i', clock, unit='bytes'),
                Metric('total', 'i', clock, unit='bytes'),
                Metric('used', 'i', clock, unit='bytes')]),
            'agent.network': CheckType(clock, [
                Metric('rx_bytes', 'i', clock, unit='bytes'),
                Metric('rx_dropped', 'i', clock, unit='bytes'),
                Metric('rx_errors', 'i', clock, unit='bytes'),
                Metric('rx_packets', 'i', clock, unit='bytes'),
                Metric('tx_bytes', 'i', clock, unit='bytes'),
                Metric('tx_dropped', 'i', clock, unit='bytes'),
                Metric('tx_errors', 'i', clock, unit='bytes'),
                Metric('tx_packets', 'i', clock, unit='bytes')]),
            'remote.http': CheckType(clock, [
                Metric('bytes', 'i', clock, unit='bytes'),
                Metric('cert_end', 'i', clock),
                Metric('cert_end_in', 'i', clock),
                Metric('cert_error', 's', clock, unit='string'),
                Metric('cert_issuer', 's', clock, unit='string'),
                Metric('cert_start', 'i', clock),
                Metric('cert_subject', 's', clock, unit='string'),
                Metric('cert_subject_alternative_names', 's', clock, unit='string'),
                Metric('code', 's', clock, unit='string'),
                Metric('duration', 'i', clock),
                Metric('truncated', 'i', clock, unit='bytes'),
                Metric('tt_connect', 'i', clock),
                Metric('tt_firstbyte', 'i', clock)]),
            'remote.ping': CheckType(clock, [
                Metric('available', 'n', clock, unit='percent'),
                Metric('average', 'n', clock),
                Metric('count', 'i', clock, unit='count'),
                Metric('maximum', 'n', clock),
                Metric('minimum', 'n', clock)])}
