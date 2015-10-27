"""
MaaS API data model
"""

from __future__ import absolute_import, division, unicode_literals

import random
import string
from uuid import uuid4

from characteristic import attributes, Attribute
from six import text_type

from mimic.util.helper import random_hex_generator, random_string

METRIC_TYPE_INTEGER = 'i'
METRIC_TYPE_NUMBER = 'n'
METRIC_TYPE_STRING = 's'


@attributes([Attribute('agent_id', default_value=None),
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
    USER_SPECIFIABLE_KEYS = ['agent_id',
                             'ip_addresses',
                             'label',
                             'managed',
                             'metadata',
                             'uri']

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
        for key in Entity.USER_SPECIFIABLE_KEYS:
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
    USER_SPECIFIABLE_KEYS = ['details',
                             'disabled',
                             'label',
                             'metadata',
                             'monitoring_zones_poll',
                             'period',
                             'target_alias',
                             'target_hostname',
                             'target_resolver',
                             'timeout',
                             'type']

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
        for key in Check.USER_SPECIFIABLE_KEYS:
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
    USER_SPECIFIABLE_KEYS = ['check_id',
                             'criteria',
                             'disabled',
                             'label',
                             'metadata',
                             'notification_plan_id']

    def to_json(self):
        """
        Serializes the Alarm to a JSON-encodable dict.
        """
        return {'id': self.id,
                'label': self.label,
                'criteria': self.criteria,
                'check_id': self.check_id,
                'entity_id': self.entity_id,
                'notification_plan_id': self.notification_plan_id,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'disabled': self.disabled,
                'metadata': self.metadata}

    def update(self, **kwargs):
        """
        Updates this Alarm.
        """
        for key in Alarm.USER_SPECIFIABLE_KEYS:
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
    USER_SPECIFIABLE_KEYS = ['details', 'label', 'metadata', 'type']

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
        for key in Notification.USER_SPECIFIABLE_KEYS:
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
    USER_SPECIFIABLE_KEYS = ['critical_state',
                             'label',
                             'metadata',
                             'ok_state',
                             'warning_state']

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
        for key in NotificationPlan.USER_SPECIFIABLE_KEYS:
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
    USER_SPECIFIABLE_KEYS = ['alarms',
                             'checks',
                             'end_time',
                             'entities',
                             'label',
                             'notification_plans',
                             'start_time']

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
        for key in Suppression.USER_SPECIFIABLE_KEYS:
            if key in kwargs:
                setattr(self, key, kwargs[key])
        self.updated_at = int(1000 * kwargs['clock'].seconds())


@attributes([Attribute('alarm_changelog_id',
                       default_factory=(lambda: text_type(uuid4())),
                       instance_of=text_type),
             Attribute('alarm_id', instance_of=text_type),
             Attribute('alarm_label', instance_of=text_type),
             Attribute('analyzed_by_monitoring_zone_id', default_value=u'mzord', instance_of=text_type),
             Attribute('check_id', instance_of=text_type),
             Attribute('entity_id', instance_of=text_type),
             Attribute('id',
                       default_factory=(lambda: u'as' + random_hex_generator(4)),
                       instance_of=text_type),
             Attribute('previous_state', instance_of=text_type),
             Attribute('state', instance_of=text_type),
             Attribute('status', instance_of=text_type),
             Attribute('timestamp', instance_of=int)])
class AlarmState(object):
    """
    Models a MaaS alarm state.
    """
    def brief_json(self):
        """
        Serializes this alarm state to a JSON-encodable dict.
        """
        return {'timestamp': self.timestamp,
                'entity_id': self.entity_id,
                'alarm_id': self.alarm_id,
                'check_id': self.check_id,
                'status': self.status,
                'state': self.state,
                'previous_state': self.previous_state,
                'alarm_changelog_id': self.alarm_changelog_id,
                'analyzed_by_monitoring_zone_id': self.analyzed_by_monitoring_zone_id}

    def detail_json(self):
        """
        Serializes this alarm state with additional details.
        """
        details = self.brief_json()
        details.update(alarm_label=self.alarm_label)
        return details


@attributes(["name",
             "type",
             Attribute("unit", default_value="other"),
             Attribute("_overrides", default_factory=dict),
             Attribute("_override_key")])
class Metric(object):
    """
    Models a MaaS metric type.
    """
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
            if self.unit == 'percent':
                return random.uniform(0, 100)
            else:
                return random.uniform(0, 100000)
        elif self.type == METRIC_TYPE_STRING:
            return random_string(random.randint(12, 30), selectable=(
                string.ascii_letters + string.digits))
        raise ValueError('No default data getter for type {0}!'.format(self.type))

    def get_value(self, **kwargs):
        """
        Gets the value of the metric at the specified timestamp.

        Overrides will be applied as necessary.
        """
        override_key = self._override_key(**kwargs)
        timestamp = kwargs['timestamp']
        if override_key in self._overrides:
            return self._overrides[override_key](timestamp)
        return self._get_default_data()

    def get_value_for_test_check(self, **kwargs):
        """
        Gets the metric data object as returned from the test-check API.
        """
        return {'type': self.type,
                'unit': self.unit,
                'data': self.get_value(**kwargs)}


def _agent_metric(**kwargs):
    """
    Creates a new metric with an agent check type keying function.
    """
    return Metric(override_key=lambda **kw: (kw['entity_id'], kw['check_id']),
                  **kwargs)


def _remote_metric(**kwargs):
    """
    Creates a new metric with a remote check type keying function.
    """
    return Metric(
        override_key=lambda **kw: (
            kw['entity_id'],
            kw['check_id'],
            kw['monitoring_zone']),
        **kwargs)


def _single_host_info_metric(**kwargs):
    """
    Creates a new metric modeling an agent host info metric type.
    """
    return Metric(override_key=lambda **kw: (kw['entity_id'], kw['agent_id']),
                  **kwargs)


def _multi_host_info_metric(**kwargs):
    """
    Creates a new metric modeling an agent host info with multiple
    return blocks.

    For instance, the CPU host info generates a block of metrics for each CPU
    on the host. Users may pin or override the values individually for each
    block (each CPU in the CPU example). This requires that a block index be
    incorporated into the metric override key.
    """
    return Metric(
        override_key=lambda **kw: (
            kw['entity_id'],
            kw['agent_id'],
            kw['block_index']),
        **kwargs)


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


@attributes([Attribute('metrics', instance_of=list)])
class SingleHostInfoType(object):
    """
    Models a MaaS host info type returning a single block of metrics,
    i.e., a hash for the info field as opposed to an array.
    """
    def get_info(self, entity_id, agent_id, timestamp):
        """
        Gets the host info.
        """
        return {'timestamp': timestamp,
                'error': None,
                'info': dict([(metric.name,
                               metric.get_value(
                                   entity_id=entity_id,
                                   agent_id=agent_id,
                                   timestamp=timestamp))
                              for metric in self.metrics])}


@attributes([Attribute('metrics', instance_of=list)])
class MultiHostInfoType(object):
    """
    Models a MaaS host info type returning multiple blocks of metrics,
    such as the CPU agent host info (one for each CPU).
    """
    def get_info(self, entity_id, agent_id, timestamp, num_blocks):
        """
        Gets the host info.
        """
        return {'timestamp': timestamp,
                'error': None,
                'info': [dict([(metric.name,
                                metric.get_value(
                                    entity_id=entity_id,
                                    agent_id=agent_id,
                                    block_index=i,
                                    timestamp=timestamp))
                               for metric in self.metrics])
                         for i in range(num_blocks)]}


@attributes([Attribute('id', instance_of=text_type, default_factory=lambda: text_type(uuid4())),
             Attribute('counts',
                       instance_of=dict,
                       default_factory=lambda: {
                           'cpus': 1,
                           'processes': 20,
                           'who': 1,
                           'filesystems': 4,
                           'disks': 1,
                           'network_interfaces': 2})])
class Agent(object):
    """
    Models a MaaS agent.
    """
    def get_host_info(self, available_types, requested_types, entity_id, clock):
        """
        Gets this agent's host information.
        """
        current_timestamp = int(1000 * clock.seconds())

        return dict([(rtype,
                      (available_types[rtype].get_info(
                          entity_id,
                          self.id,
                          current_timestamp,
                          self.counts[rtype])
                       if rtype in self.counts
                       else available_types[rtype].get_info(
                           entity_id,
                           self.id,
                           current_timestamp)))
                     for rtype in requested_types])


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
        self.agents = []
        self.alarm_states = []

        self.check_types = {
            'agent.cpu': CheckType(clock=clock, metrics=[
                _agent_metric(name='user_percent_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                _agent_metric(name='wait_percent_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                _agent_metric(name='sys_percent_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                _agent_metric(name='idle_percent_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                _agent_metric(name='irq_percent_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                _agent_metric(name='usage_average', type=METRIC_TYPE_NUMBER, unit='percent'),
                _agent_metric(name='min_cpu_usage', type=METRIC_TYPE_NUMBER, unit='percent'),
                _agent_metric(name='max_cpu_usage', type=METRIC_TYPE_NUMBER, unit='percent'),
                _agent_metric(name='stolen_percent_average', type=METRIC_TYPE_NUMBER, unit='percent')]),
            'agent.disk': CheckType(clock=clock, metrics=[
                _agent_metric(name='queue', type=METRIC_TYPE_INTEGER),
                _agent_metric(name='read_bytes', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='reads', type=METRIC_TYPE_INTEGER, unit='count'),
                _agent_metric(name='rtime', type=METRIC_TYPE_INTEGER),
                _agent_metric(name='wtime', type=METRIC_TYPE_INTEGER),
                _agent_metric(name='write_bytes', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='writes', type=METRIC_TYPE_INTEGER, unit='count')]),
            'agent.filesystem': CheckType(clock=clock, metrics=[
                _agent_metric(name='avail', type=METRIC_TYPE_INTEGER, unit='kilobytes'),
                _agent_metric(name='free', type=METRIC_TYPE_INTEGER, unit='kilobytes'),
                _agent_metric(name='options', type=METRIC_TYPE_STRING, unit='string'),
                _agent_metric(name='total', type=METRIC_TYPE_INTEGER, unit='kilobytes'),
                _agent_metric(name='used', type=METRIC_TYPE_INTEGER, unit='kilobytes'),
                _agent_metric(name='files', type=METRIC_TYPE_INTEGER, unit='count'),
                _agent_metric(name='free_files', type=METRIC_TYPE_INTEGER, unit='count')]),
            'agent.load_average': CheckType(clock=clock, metrics=[
                _agent_metric(name='1m', type=METRIC_TYPE_NUMBER),
                _agent_metric(name='5m', type=METRIC_TYPE_NUMBER),
                _agent_metric(name='10m', type=METRIC_TYPE_NUMBER)]),
            'agent.memory': CheckType(clock=clock, metrics=[
                _agent_metric(name='actual_free', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='actual_used', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='free', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='ram', type=METRIC_TYPE_INTEGER, unit='megabytes'),
                _agent_metric(name='swap_free', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='swap_page_in', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='swap_page_out', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='swap_total', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='swap_used', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='total', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='used', type=METRIC_TYPE_INTEGER, unit='bytes')]),
            'agent.network': CheckType(clock=clock, metrics=[
                _agent_metric(name='rx_bytes', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='rx_dropped', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='rx_errors', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='rx_packets', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='tx_bytes', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='tx_dropped', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='tx_errors', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _agent_metric(name='tx_packets', type=METRIC_TYPE_INTEGER, unit='bytes')]),
            'remote.http': CheckType(clock=clock, metrics=[
                _remote_metric(name='bytes', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _remote_metric(name='cert_end', type=METRIC_TYPE_INTEGER),
                _remote_metric(name='cert_end_in', type=METRIC_TYPE_INTEGER),
                _remote_metric(name='cert_error', type=METRIC_TYPE_STRING, unit='string'),
                _remote_metric(name='cert_issuer', type=METRIC_TYPE_STRING, unit='string'),
                _remote_metric(name='cert_start', type=METRIC_TYPE_INTEGER),
                _remote_metric(name='cert_subject', type=METRIC_TYPE_STRING, unit='string'),
                _remote_metric(name='cert_subject_alternative_names',
                               type=METRIC_TYPE_STRING,
                               unit='string'),
                _remote_metric(name='code', type=METRIC_TYPE_STRING, unit='string'),
                _remote_metric(name='duration', type=METRIC_TYPE_INTEGER),
                _remote_metric(name='truncated', type=METRIC_TYPE_INTEGER, unit='bytes'),
                _remote_metric(name='tt_connect', type=METRIC_TYPE_INTEGER),
                _remote_metric(name='tt_firstbyte', type=METRIC_TYPE_INTEGER)]),
            'remote.ping': CheckType(clock=clock, metrics=[
                _remote_metric(name='available', type=METRIC_TYPE_NUMBER, unit='percent'),
                _remote_metric(name='average', type=METRIC_TYPE_NUMBER),
                _remote_metric(name='count', type=METRIC_TYPE_INTEGER, unit='count'),
                _remote_metric(name='maximum', type=METRIC_TYPE_NUMBER),
                _remote_metric(name='minimum', type=METRIC_TYPE_NUMBER)])}

        self.host_info_types = {
            'cpus': MultiHostInfoType(metrics=[
                _multi_host_info_metric(name='idle', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='irq', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='mhz', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='model', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='name', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='soft_irq', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='stolen', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='sys', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='total', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='total_cores', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='user', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='vendor', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='wait', type=METRIC_TYPE_INTEGER)]),
            'disks': MultiHostInfoType(metrics=[
                _multi_host_info_metric(name='name', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='read_bytes', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='reads', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='rtime', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='time', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='write_bytes', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='writes', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='wtime', type=METRIC_TYPE_INTEGER)]),
            'filesystems': MultiHostInfoType(metrics=[
                _multi_host_info_metric(name='avail', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='dev_name', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='dir_name', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='files', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='free', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='free_files', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='options', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='sys_type_name', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='total', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='used', type=METRIC_TYPE_INTEGER)]),
            'memory': SingleHostInfoType(metrics=[
                _single_host_info_metric(name='actual_free', type=METRIC_TYPE_INTEGER),
                _single_host_info_metric(name='actual_used', type=METRIC_TYPE_INTEGER),
                _single_host_info_metric(name='free', type=METRIC_TYPE_INTEGER),
                _single_host_info_metric(name='free_percent', type=METRIC_TYPE_NUMBER, unit='percent'),
                _single_host_info_metric(name='ram', type=METRIC_TYPE_INTEGER),
                _single_host_info_metric(name='total', type=METRIC_TYPE_INTEGER),
                _single_host_info_metric(name='used', type=METRIC_TYPE_INTEGER),
                _single_host_info_metric(name='used_percent', type=METRIC_TYPE_NUMBER, unit='percent')]),
            'network_interfaces': MultiHostInfoType(metrics=[
                _multi_host_info_metric(name='address', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='address6', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='broadcast', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='flags', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='hwaddr', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='mtu', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='name', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='netmask', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='rx_bytes', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='rx_packets', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='tx_bytes', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='tx_packets', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='type', type=METRIC_TYPE_STRING)]),
            'processes': MultiHostInfoType(metrics=[
                _multi_host_info_metric(name='cred_group', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='cred_user', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='exe_cwd', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='exe_name', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='exe_root', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='memory_major_faults', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='memory_minor_faults', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='memory_page_faults', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='memory_resident', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='memory_share', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='memory_size', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='pid', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='state_name', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='state_priority', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='state_threads', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='time_start_time', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='time_sys', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='time_total', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='time_user', type=METRIC_TYPE_INTEGER)]),
            'system': SingleHostInfoType(metrics=[
                _single_host_info_metric(name='arch', type=METRIC_TYPE_STRING),
                _single_host_info_metric(name='name', type=METRIC_TYPE_STRING),
                _single_host_info_metric(name='vendor', type=METRIC_TYPE_STRING),
                _single_host_info_metric(name='vendor_name', type=METRIC_TYPE_STRING),
                _single_host_info_metric(name='vendor_version', type=METRIC_TYPE_STRING),
                _single_host_info_metric(name='version', type=METRIC_TYPE_STRING)]),
            'who': MultiHostInfoType(metrics=[
                _multi_host_info_metric(name='device', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='host', type=METRIC_TYPE_STRING),
                _multi_host_info_metric(name='time', type=METRIC_TYPE_INTEGER),
                _multi_host_info_metric(name='user', type=METRIC_TYPE_STRING)])}

    def latest_alarm_states_for_entity(self, entity_id):
        """
        Computes the latest alarm states for the specified entity.

        Newer alarm states are assumed to be always appended to the list of
        alarm states.
        """
        alarm_states_for_entity = [state for state in self.alarm_states
                                   if state.entity_id == entity_id]
        latest_alarm_states_by_alarm = {}
        for state in alarm_states_for_entity:
            latest_alarm_states_by_alarm[state.alarm_id] = state
        return latest_alarm_states_by_alarm.values()
