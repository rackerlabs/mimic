"""
MaaS API data model
"""

import random
import string

from characteristic import attributes, Attribute
from six import text_type

from mimic.util.helper import random_hex_generator, random_string

METRIC_TYPE_INTEGER = 'i'
METRIC_TYPE_NUMBER = 'n'
METRIC_TYPE_STRING = 's'


@attributes([Attribute('agent_id', default_value=None),
             Attribute('alarm_states', default_factory=list, instance_of=list),
             Attribute('created_at', instance_of=int),
             Attribute('id',
                       default_factory=(lambda: u'en' + random_hex_generator(4)),
                       instance_of=text_type),
             Attribute('ip_addresses', default_factory=dict, instance_of=dict),
             Attribute('label', default_value=u'', instance_of=text_type),
             Attribute('managed', default_value=False, instance_of=bool),
             Attribute('metadata', default_factory=dict, instance_of=dict),
             Attribute('updated_at', instance_of=int),
             Attribute('uri', default_value=None)])
class Entity(object):
    """
    Models a MaaS Entity.
    """
    def to_json(self):
        """
        Serializes the Entity to a JSON-encodable dict.
        """
        return {'label': self.label,
                'id': self.id,
                'agent_id': self.agent_id,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'managed': self.managed,
                'metadata': self.metadata,
                'ip_addresses': self.ip_addresses,
                'uri': self.uri}

    def update(self, **kwargs):
        """
        Updates this Entity.
        """
        for key in ['agent_id', 'managed', 'metadata', 'ip_addresses', 'uri', 'label']:
            if key in kwargs:
                setattr(self, key, kwargs[key])
        self.updated_at = int(1000 * kwargs['clock'].seconds())


@attributes([Attribute('created_at', instance_of=int),
             Attribute('details', default_factory=dict, instance_of=dict),
             Attribute('disabled', default_value=False, instance_of=bool),
             Attribute('entity_id', instance_of=text_type),
             Attribute('id',
                       default_factory=(lambda: u'ch' + random_hex_generator(4)),
                       instance_of=text_type),
             Attribute('label', default_value=u'', instance_of=text_type),
             Attribute('metadata', default_factory=dict, instance_of=dict),
             Attribute('monitoring_zones_poll', default_factory=list, instance_of=list),
             Attribute('period', default_value=60, instance_of=int),
             Attribute('target_alias', default_value=None),
             Attribute('target_hostname', default_value=None),
             Attribute('target_resolver', default_value=None),
             Attribute('timeout', default_value=10, instance_of=int),
             Attribute('type', instance_of=text_type),
             Attribute('updated_at', instance_of=int)])
class Check(object):
    """
    Models a MaaS Check.
    """
    def to_json(self):
        """
        Serializes the Check to a JSON-encodable dict.
        """
        return {'label': self.label,
                'id': self.id,
                'type': self.type,
                'monitoring_zones_poll': self.monitoring_zones_poll,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'timeout': self.timeout,
                'period': self.period,
                'disabled': self.disabled,
                'metadata': self.metadata,
                'target_alias': self.target_alias,
                'target_resolver': self.target_resolver,
                'target_hostname': self.target_hostname,
                'details': self.details}

    def update(self, **kwargs):
        """
        Updates this Check.
        """
        for key in ['type', 'details', 'disabled', 'label', 'metadata', 'period', 'timeout',
                    'monitoring_zones_poll', 'target_alias', 'target_hostname', 'target_resolver']:
            if key in kwargs:
                setattr(self, key, kwargs[key])
        self.updated_at = int(1000 * kwargs['clock'].seconds())


@attributes([Attribute('check_id', instance_of=text_type),
             Attribute('created_at', instance_of=int),
             Attribute('criteria', default_value=u'', instance_of=text_type),
             Attribute('disabled', default_value=False, instance_of=bool),
             Attribute('entity_id', instance_of=text_type),
             Attribute('id',
                       default_factory=(lambda: u'al' + random_hex_generator(4)),
                       instance_of=text_type),
             Attribute('label', default_value=u'', instance_of=text_type),
             Attribute('metadata', default_factory=dict, instance_of=dict),
             Attribute('notification_plan_id', instance_of=text_type),
             Attribute('updated_at', instance_of=int)])
class Alarm(object):
    """
    Models a MaaS Alarm.
    """
    def to_json(self):
        """
        Serializes the Alarm to a JSON-encodable dict.
        """
        return {'id': self.id,
                'label': self.label,
                'criteria': self.criteria,
                'check_id': self.check_id,
                'notification_plan_id': self.notification_plan_id,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'disabled': self.disabled,
                'metadata': self.metadata}

    def update(self, **kwargs):
        """
        Updates this Alarm.
        """
        for key in ['check_id', 'notification_plan_id', 'criteria', 'disabled', 'label',
                    'metadata']:
            if key in kwargs:
                setattr(self, key, kwargs[key])
        self.updated_at = int(1000 * kwargs['clock'].seconds())


@attributes([Attribute('created_at', instance_of=int),
             Attribute('details', default_factory=dict, instance_of=dict),
             Attribute('id',
                       default_factory=(lambda: u'nt' + random_hex_generator(4)),
                       instance_of=text_type),
             Attribute('label', default_value=u'', instance_of=text_type),
             Attribute('metadata', default_factory=dict, instance_of=dict),
             Attribute('type', default_value='email', instance_of=text_type),
             Attribute('updated_at', instance_of=int)])
class Notification(object):
    """
    Models a MaaS Notification.
    """
    def to_json(self):
        """
        Serializes the Notification to a JSON-encodable dict.
        """
        return {'id': self.id,
                'label': self.label,
                'type': self.type,
                'details': self.details,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'metadata': self.metadata}

    def update(self, **kwargs):
        """
        Updates this Notification.
        """
        for key in ['details', 'label', 'metadata', 'type']:
            if key in kwargs:
                setattr(self, key, kwargs[key])
        self.updated_at = int(1000 * kwargs['clock'].seconds())


@attributes([Attribute('created_at', instance_of=int),
             Attribute('critical_state', default_factory=list, instance_of=list),
             Attribute('id',
                       default_factory=(lambda: u'np' + random_hex_generator(4)),
                       instance_of=text_type),
             Attribute('label', default_value=u'', instance_of=text_type),
             Attribute('metadata', default_factory=dict, instance_of=dict),
             Attribute('ok_state', default_factory=list, instance_of=list),
             Attribute('updated_at', instance_of=int),
             Attribute('warning_state', default_factory=list, instance_of=list)])
class NotificationPlan(object):
    """
    Models a MaaS notification plan.
    """
    def to_json(self):
        """
        Serializes the Notification Plan to a JSON-encodable dict.
        """
        return {'id': self.id,
                'label': self.label,
                'critical_state': self.critical_state,
                'warning_state': self.warning_state,
                'ok_state': self.ok_state,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'metadata': self.metadata}

    def update(self, **kwargs):
        """
        Updates this Notification Plan.
        """
        for key in ['critical_state', 'label', 'metadata', 'ok_state', 'warning_state']:
            if key in kwargs:
                setattr(self, key, kwargs[key])
        self.updated_at = int(1000 * kwargs['clock'].seconds())


@attributes([Attribute('alarms', default_factory=list, instance_of=list),
             Attribute('checks', default_factory=list, instance_of=list),
             Attribute('created_at', instance_of=int),
             Attribute('end_time', default_value=0, instance_of=int),
             Attribute('entities', default_factory=list, instance_of=list),
             Attribute('id',
                       default_factory=(lambda: u'sp' + random_hex_generator(4)),
                       instance_of=text_type),
             Attribute('label', default_value=u'', instance_of=text_type),
             Attribute('notification_plans', default_factory=list, instance_of=list),
             Attribute('start_time', default_value=0, instance_of=int),
             Attribute('updated_at', instance_of=int)])
class Suppression(object):
    """
    Models a MaaS suppression.
    """
    def to_json(self):
        """
        Serializes the Suppression to a JSON-encodable dict.
        """
        return {'id': self.id,
                'label': self.label,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'notification_plans': self.notification_plans,
                'entities': self.entities,
                'checks': self.checks,
                'alarms': self.alarms}

    def update(self, **kwargs):
        """
        Updates this Suppression.
        """
        for key in ['alarms', 'checks', 'end_time', 'entities', 'label',
                    'notification_plans', 'start_time']:
            if key in kwargs:
                setattr(self, key, kwargs[key])
        self.updated_at = int(1000 * kwargs['clock'].seconds())


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
