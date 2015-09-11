"""
MaaS API data model
"""

import random
import string

from characteristic import attributes, Attribute

from mimic.util.helper import random_string

METRIC_TYPE_INTEGER = 'i'
METRIC_TYPE_NUMBER = 'n'
METRIC_TYPE_STRING = 's'


@attributes(["name",
             "type",
             Attribute("_unit", default_value="other"),
             Attribute("_overrides", default_factory=dict)])
class Metric(object):
    """
    Models a MaaS metric type.
    """
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
        if self.type == METRIC_TYPE_INTEGER:
            return random.randint(0, 100000)
        elif self.type == METRIC_TYPE_NUMBER:
            if self._unit == 'percent':
                return random.uniform(0, 100)
            else:
                return random.uniform(0, 100000)
        elif self.type == METRIC_TYPE_STRING:
            return random_string(random.randint(12, 30), selectable=(string.letters + string.digits))
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


@attributes(["metrics",
             Attribute("_clock"),
             Attribute("test_check_available", default_factory=dict),
             Attribute("test_check_status", default_factory=dict),
             Attribute("test_check_response_code", default_factory=dict)])
class CheckType(object):
    """
    Data model for a MaaS check type (e.g., remote.ping).
    """
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
        Initializes the MaaS configuration using the provided clock.

        This initializer reflects the variety of available check types and
        metrics supported by MaaS. Some MaaS check types have been omitted
        for simplicity and clarity. The full list of check types and metrics
        can be found in `the Rackspace Cloud Monitoring Developer Guide, appendix B
            <http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/appendix-check-types.html>`_
        """
        self.check_types = {
            'agent.cpu': CheckType(clock=clock, metrics=[
                Metric(name='user_percent_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                Metric(name='wait_percent_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                Metric(name='sys_percent_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                Metric(name='idle_percent_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                Metric(name='irq_percent_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                Metric(name='usage_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                Metric(name='min_cpu_usage', type=METRIC_TYPE_NUMBER, unit='percent'),
                Metric(name='max_cpu_usage', type=METRIC_TYPE_NUMBER, unit='percent'),
                Metric(name='stolen_percent_average', type=METRIC_TYPE_NUMBER, unit='percent')]),
            'agent.disk': CheckType(clock=clock, metrics=[
                Metric(name='queue', type=METRIC_TYPE_INTEGER),
                Metric(name='read_bytes', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='reads', type=METRIC_TYPE_INTEGER, unit='count'),
                Metric(name='rtime', type=METRIC_TYPE_INTEGER),
                Metric(name='wtime', type=METRIC_TYPE_INTEGER),
                Metric(name='write_bytes', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='writes', type=METRIC_TYPE_INTEGER, unit='count')]),
            'agent.filesystem': CheckType(clock=clock, metrics=[
                Metric(name='avail', type=METRIC_TYPE_INTEGER, unit='kilobytes'),
                Metric(name='free', type=METRIC_TYPE_INTEGER, unit='kilobytes'),
                Metric(name='options', type=METRIC_TYPE_STRING, unit='string'),
                Metric(name='total', type=METRIC_TYPE_INTEGER, unit='kilobytes'),
                Metric(name='used', type=METRIC_TYPE_INTEGER, unit='kilobytes'),
                Metric(name='files', type=METRIC_TYPE_INTEGER, unit='count'),
                Metric(name='free_files', type=METRIC_TYPE_INTEGER, unit='count')]),
            'agent.load_average': CheckType(clock=clock, metrics=[
                Metric(name='1m', type=METRIC_TYPE_NUMBER),
                Metric(name='5m', type=METRIC_TYPE_NUMBER),
                Metric(name='10m', type=METRIC_TYPE_NUMBER)]),
            'agent.memory': CheckType(clock=clock, metrics=[
                Metric(name='actual_free', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='actual_used', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='free', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='ram', type=METRIC_TYPE_INTEGER, unit='megabytes'),
                Metric(name='swap_free', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='swap_page_in', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='swap_page_out', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='swap_total', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='swap_used', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='total', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='used', type=METRIC_TYPE_INTEGER, unit='bytes')]),
            'agent.network': CheckType(clock=clock, metrics=[
                Metric(name='rx_bytes', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='rx_dropped', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='rx_errors', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='rx_packets', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='tx_bytes', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='tx_dropped', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='tx_errors', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='tx_packets', type=METRIC_TYPE_INTEGER, unit='bytes')]),
            'remote.http': CheckType(clock=clock, metrics=[
                Metric(name='bytes', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='cert_end', type=METRIC_TYPE_INTEGER),
                Metric(name='cert_end_in', type=METRIC_TYPE_INTEGER),
                Metric(name='cert_error', type=METRIC_TYPE_STRING, unit='string'),
                Metric(name='cert_issuer', type=METRIC_TYPE_STRING, unit='string'),
                Metric(name='cert_start', type=METRIC_TYPE_INTEGER),
                Metric(name='cert_subject', type=METRIC_TYPE_STRING, unit='string'),
                Metric(name='cert_subject_alternative_names', type=METRIC_TYPE_STRING, unit='string'),
                Metric(name='code', type=METRIC_TYPE_STRING, unit='string'),
                Metric(name='duration', type=METRIC_TYPE_INTEGER),
                Metric(name='truncated', type=METRIC_TYPE_INTEGER, unit='bytes'),
                Metric(name='tt_connect', type=METRIC_TYPE_INTEGER),
                Metric(name='tt_firstbyte', type=METRIC_TYPE_INTEGER)]),
            'remote.ping': CheckType(clock=clock, metrics=[
                Metric(name='available', type=METRIC_TYPE_NUMBER, unit='percent'),
                Metric(name='average', type=METRIC_TYPE_NUMBER),
                Metric(name='count', type=METRIC_TYPE_INTEGER, unit='count'),
                Metric(name='maximum', type=METRIC_TYPE_NUMBER),
                Metric(name='minimum', type=METRIC_TYPE_NUMBER)])}
