"""
MAAS Mock API
"""

from __future__ import division, unicode_literals

import json
import collections
from six.moves.urllib.parse import parse_qs
import random
import re
from uuid import uuid4

import attr
from six import text_type

from zope.interface import implementer

from twisted.plugin import IPlugin

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.rest.identity_api import base_uri_from_request
from mimic.rest.mimicapp import MimicApp
from mimic.imimic import IAPIMock
from mimic.canned_responses.maas_json_home import json_home
from mimic.canned_responses.maas_monitoring_zones import monitoring_zones
from mimic.canned_responses.maas_alarm_examples import alarm_examples
from mimic.model.maas_errors import ObjectDoesNotExist, ParentDoesNotExist
from mimic.model.maas_objects import (Agent,
                                      Alarm,
                                      AlarmState,
                                      Check,
                                      Entity,
                                      MaasStore,
                                      Notification,
                                      NotificationPlan,
                                      Suppression)
from mimic.util.helper import json_from_request
from mimic.util.helper import Matcher, random_hex_generator, random_hipsum


MISSING_REQUIRED_ARGUMENT_REGEX = re.compile(
    r'__init__\(\) missing \d+ required positional argument: \'(\w+)\'')
REMOTE_CHECK_TYPE_REGEX = re.compile(r'^remote\.')


@implementer(IAPIMock, IPlugin)
class MaasApi(object):
    """
    Rest endpoints for mocked MAAS Api.
    """

    def __init__(self, regions=["ORD"]):
        """
        Set regions
        """
        self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the MaaS API.
        """
        return [
            Entry(
                tenant_id, "rax:monitor", "cloudMonitoring",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()),
                             "v1.0")
                    for region in self._regions
                ]
            )
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an : obj: `twisted.web.iweb.IResource` for the given URI prefix;
        implement : obj: `IAPIMock`.
        """
        return MaasMock(self, uri_prefix, session_store, region).app.resource()


class MCache(object):
    """
    M(onitoring) Cache Object to hold dictionaries of all entities, checks and alarms.
    """

    def __init__(self, clock):
        """
        Create the initial structs for cache
        """
        current_time_milliseconds = int(1000 * clock.seconds())

        self.entities = collections.OrderedDict()
        self.notifications = collections.OrderedDict(
            [(u'ntTechnicalContactsEmail',
              Notification(id=u'ntTechnicalContactsEmail',
                           label=u'Email All Technical Contacts',
                           created_at=current_time_milliseconds,
                           updated_at=current_time_milliseconds,
                           type=u'technicalContactsEmail'))])
        self.notification_plans = collections.OrderedDict(
            [(u'npTechnicalContactsEmail',
              NotificationPlan(id=u'npTechnicalContactsEmail',
                               label=u'Technical Contacts - Email',
                               created_at=current_time_milliseconds,
                               updated_at=current_time_milliseconds))])
        self.notificationtypes_list = [{'id': 'webhook', 'fields': [{'name': 'url',
                                                                     'optional': False,
                                                                     'description': 'An HTTP or \
                                                                      HTTPS URL to POST to'}]},
                                       {'id': 'email', 'fields': [{'name': 'address',
                                                                   'optional': False,
                                                                   'description': 'Email \
                                                                    address to send notifications to'}]},
                                       {'id': 'pagerduty', 'fields': [{'name': 'service_key',
                                                                       'optional': False,
                                                                       'description': 'The PagerDuty \
                                                                        service key to use.'}]},
                                       {'id': 'sms', 'fields': [{'name': 'phone_number',
                                                                 'optional': False,
                                                                 'description': 'Phone number to send \
                                                                  the notification to, \
                                                                  with leading + and country \
                                                                  code (E.164 format)'}]}]
        self.suppressions = collections.OrderedDict()
        self.audits_list = []
        self.maas_store = MaasStore(clock)
        self.test_alarm_responses = {}
        self.test_alarm_errors = {}


def _only_keys(dict_ins, keys):
    """
    Filters out unwanted keys of a dict.
    """
    return {k: dict_ins[k] for k in dict_ins if k in keys}


def create_entity(clock, params):
    """
    Returns a dictionary representing an entity

    :return: an Entity model, which is described in `the Rackspace Cloud
        Monitoring Developer Guide, section 5.4
        <http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-entities.html>`_
    :rtype: ``dict`` mapping ``unicode`` to ``unicode``, ``float``,
        ``bool``, ``dict`` or ``NoneType``.
    """
    current_time_milliseconds = int(1000 * clock.seconds())
    params_copy = _only_keys(params, Entity.USER_SPECIFIABLE_KEYS)
    params_copy['created_at'] = params_copy[
        'updated_at'] = current_time_milliseconds
    return Entity(**params_copy)


def create_check(clock, params):
    """
    Returns a dictionary representing a check

    :return: a Check model, which is described in `the Rackspace Cloud
        Monitoring Developer Guide, section 5.7
        <http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-checks.html>`_
    :rtype: ``dict`` mapping ``unicode`` to ``unicode``, ``float``,
        ``int``, ``bool``, ``dict`` or ``NoneType``.
    """
    current_time_milliseconds = int(1000 * clock.seconds())
    params_copy = _only_keys(params, Check.USER_SPECIFIABLE_KEYS)
    params_copy['created_at'] = params_copy[
        'updated_at'] = current_time_milliseconds
    return Check(**params_copy)


def create_alarm(clock, entity_id, params):
    """
    Returns a dictionary representing an alarm

    :return: an Alarm model, which is described in `the Rackspace Cloud
        Monitoring Developer Guide, section 5.12
        <http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-alarms.html>`_
    :rtype: ``dict`` mapping ``unicode`` to ``unicode``, ``float``,
        ``bool``, ``dict``, or ``NoneType``.
    """
    current_time_milliseconds = int(1000 * clock.seconds())
    params_copy = _only_keys(params, Alarm.USER_SPECIFIABLE_KEYS)
    params_copy['entity_id'] = entity_id
    params_copy['created_at'] = params_copy[
        'updated_at'] = current_time_milliseconds
    return Alarm(**params_copy)


def create_notification_plan(clock, params):
    """
    Creates a notification plan

    :return: a Notification Plan model, which is described in `the
        Rackspace Cloud Monitoring Developer Guide, section 5.11
        <http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-notification-plans.html>`_
    :rtype: ``dict`` mapping ``unicode`` to ``unicode``, ``float``,
        ``dict`` or ``NoneType``.
    """
    current_time_milliseconds = int(1000 * clock.seconds())
    params_copy = _only_keys(params, NotificationPlan.USER_SPECIFIABLE_KEYS)
    params_copy['created_at'] = params_copy[
        'updated_at'] = current_time_milliseconds
    return NotificationPlan(**params_copy)


def create_notification(clock, params):
    """
    Creates a notification target

    :return: a Notification model, which is described in `the Rackspace
        Cloud Monitoring Developer Guide, section 5.10
        <http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-notifications.html>`_
    :rtype: ``dict`` mapping ``unicode`` to ``unicode``, ``float``,
        ``dict`` or ``NoneType``.
    """
    current_time_milliseconds = int(1000 * clock.seconds())
    params_copy = _only_keys(params, Notification.USER_SPECIFIABLE_KEYS)
    params_copy['created_at'] = params_copy[
        'updated_at'] = current_time_milliseconds
    return Notification(**params_copy)


def create_suppression(clock, params):
    """
    Creates a suppression

    :return: a Suppression model, which is described in `the Rackspace
        Cloud Monitoring Developer Guide, section 5.16
        <http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-suppressions.html>`_
    :rtype: ``dict`` mapping ``unicode`` to ``unicode`` or ``list``.
    """
    params_copy = _only_keys(params, Suppression.USER_SPECIFIABLE_KEYS)
    params_copy['created_at'] = params_copy[
        'updated_at'] = int(1000 * clock.seconds())
    return Suppression(**params_copy)


def _get_object(collection, object_type, object_key, alt_key=None):
    """
    Gets the specified object from the collection or throws ObjectDoesNotExist.

    The collection should behave like a dict where object_key retrieves
    an object from the collection.
    """
    try:
        return collection[object_key]
    except KeyError:
        raise ObjectDoesNotExist(object_type=object_type,
                                 key=(alt_key or object_key))


def _delete_object(collection, object_type, object_key, alt_key=None):
    """
    Deletes the specified object from the collection or throws ObjectDoesNotExist.
    """
    try:
        del collection[object_key]
    except KeyError:
        raise ObjectDoesNotExist(object_type=object_type,
                                 key=(alt_key or object_key))


def _get_entity(entities, entity_id):
    """
    Gets the entity from the collection or throws ObjectDoesNotExist.
    """
    return _get_object(entities, 'Entity', entity_id)


def _delete_entity(entities, entity_id):
    """
    Deletes the entity from the collection or throws ObjectDoesNotExist.
    """
    _delete_object(entities, 'Entity', entity_id)


def _get_parent_entity(entities, entity_id):
    """
    Gets the parent entity from the collection, or throws ParentDoesNotExist.
    """
    try:
        return entities[entity_id]
    except KeyError:
        raise ParentDoesNotExist(object_type='Entity', key=entity_id)


def _get_check(entities, entity_id, check_id):
    """
    Gets the check from the collection, or throws an error if it does not exist.
    """
    entity = _get_parent_entity(entities, entity_id)
    return _get_object(entity.checks,
                       'Check',
                       check_id,
                       '{0}:{1}'.format(entity_id, check_id))


def _delete_check(entities, entity_id, check_id):
    """
    Deletes the check from the collection, or throws an error if it does not exist.
    """
    entity = _get_parent_entity(entities, entity_id)

    _delete_object(entity.checks,
                   'Check',
                   check_id,
                   '{0}:{1}'.format(entity_id, check_id))

    alarms_to_delete = [alarm_id for alarm_id in entity.alarms
                        if entity.alarms[alarm_id].check_id == check_id]
    for alarm_id in alarms_to_delete:
        del entity.alarms[alarm_id]


def _delete_alarm(entities, entity_id, alarm_id):
    """
    Deletes the alarm from the collection, or throws an error if it does not exist.
    """
    entity = _get_parent_entity(entities, entity_id)

    _delete_object(entity.alarms,
                   'Alarm',
                   alarm_id,
                   '{0}:{1}'.format(entity_id, alarm_id))


def _get_alarm(entities, entity_id, alarm_id):
    """
    Gets the alarm from the collection, or throws an error if it does not exist.
    """
    entity = _get_parent_entity(entities, entity_id)
    return _get_object(entity.alarms,
                       'Alarm',
                       alarm_id,
                       '{0}:{1}'.format(entity_id, alarm_id))


def _get_notification(notifications, nt_id):
    """
    Gets the notification from the collection or throws ObjectDoesNotExist.
    """
    return _get_object(notifications, 'Notification', nt_id)


def _delete_notification(notifications, nt_id):
    """
    Deletes the notification from the collection, or throws ObjectDoesNotExist.
    """
    _delete_object(notifications, 'Notification', nt_id)


def _get_notification_plan(notification_plans, np_id):
    """
    Gets the notification plan from the collection.

    This function gets the notification plan or throws ObjectDoesNotExist
    if it does not exist.
    """
    return _get_object(notification_plans, 'NotificationPlan', np_id)


def _delete_notification_plan(notification_plans, np_id):
    """
    Deletes the notification plan from the collection, or throws ObjectDoesNotExist.
    """
    _delete_object(notification_plans, 'NotificationPlan', np_id)


def _get_suppression(suppressions, sp_id):
    """
    Gets the suppression from the collection or throws ObjectDoesNotExist.
    """
    return _get_object(suppressions, 'Suppression', sp_id)


def _delete_suppression(suppressions, sp_id):
    """
    Deletes the suppression from the collection, or throws ObjectDoesNotExist.
    """
    _delete_object(suppressions, 'Suppression', sp_id)


def _map_getter(collection, request, object_type, object_key):
    """
    Getter handler for objects in a Mapping type collection.
    """
    try:
        obj = _get_object(collection, object_type, object_key)
        return json.dumps(obj.to_json())
    except ObjectDoesNotExist as e:
        request.setResponseCode(e.code)
        return json.dumps(e.to_json())


def _find_missing_required_key(cls, post_data, additional_keys):
    """
    Finds a missing required key in the case that trying to create an instance
    failed with a TypeError.
    """
    fields_by_name = {field.name: field for field in attr.fields(cls)}
    specified_keys = {key for sublist in [post_data.keys(), additional_keys]
                      for key in sublist}
    missing_keys = [key for key in fields_by_name
                    if fields_by_name[key].default is attr.NOTHING and key not in specified_keys]
    return missing_keys[0]


def _metric_list_for_check(maas_store, entity, check):
    """
    Computes the metrics list for a given check.

    Remote checks return a metric for each monitoring zone and
    each type of metric for the check type. Agent checks return
    a metric for each metric type on the check type. Check types
    that Mimic doesn't know about generate an empty list.
    """
    if check.type not in maas_store.check_types:
        return []

    if REMOTE_CHECK_TYPE_REGEX.match(check.type):
        return [{'name': '{0}.{1}'.format(mz, metric.name),
                 'type': metric.type,
                 'unit': metric.unit}
                for metric in maas_store.check_types[check.type].metrics
                for mz in check.monitoring_zones_poll]

    return [{'name': metric.name,
             'type': metric.type,
             'unit': metric.unit}
            for metric in maas_store.check_types[check.type].metrics]


def _metric_list_for_entity(maas_store, entity):
    """
    Creates the metrics list for one entity.
    """
    return {'entity_id': entity.id,
            'entity_label': entity.label,
            'checks': [{'id': check.id,
                        'label': check.label,
                        'type': check.type,
                        'metrics': _metric_list_for_check(maas_store, entity, check)}
                       for check in entity.checks.values()]}


def _multiplot_interval(from_date, to_date, points):
    """
    Computes the size of the interval between points in a multiplot.

    :return: the multiplot interval size.
    :rtype: ``float``
    """
    if points < 2:
        return 0.0
    return (to_date - from_date) / (points - 1)


def _compute_multiplot(maas_store, entity_id, check, metric_name, from_date, to_date, points):
    """
    Computes multiplot data for a single (entity, check, metric) group.
    """
    fallback = {'entity_id': entity_id,
                'check_id': check.id,
                'metric': metric_name,
                'unit': 'unknown',
                'type': 'unknown',
                'data': []}

    if check.type not in maas_store.check_types:
        return fallback

    interval = _multiplot_interval(from_date, to_date, points)
    metric = None
    base_metric_name = metric_name
    metric_value_kwargs = {'entity_id': entity_id,
                           'check_id': check.id}
    if re.match(r'^remote\.', check.type):
        match = re.match(r'^(mz\w+)\.(\w+)$', metric_name)
        if not match:
            return fallback
        metric_value_kwargs['monitoring_zone'] = match.group(1)
        base_metric_name = match.group(2)

    try:
        metric = maas_store.check_types[
            check.type].get_metric_by_name(base_metric_name)
    except NameError:
        return fallback

    return {'entity_id': entity_id,
            'check_id': check.id,
            'metric': metric_name,
            'unit': metric.unit,
            'type': metric.type,
            'data': [{'numPoints': 4,
                      'timestamp': int(from_date + (i * interval)),
                      'average': metric.get_value(
                          timestamp=int(from_date + (i * interval)),
                          **metric_value_kwargs)}
                     for i in range(points)]}


def parse_and_flatten_qs(url):
    """
    Parses a querystring and flattens 1-arg arrays.
    """
    qs = parse_qs(url)
    flat_qs = {}
    for key in qs:
        flat_qs[key] = qs[key][0] if len(qs[key]) == 1 else qs[key]
    return flat_qs


def _mcache_factory(clock):
    """
    Returns a function that makes a defaultdict that makes MCache objects
    for each tenant.
    """
    return lambda: collections.defaultdict(lambda: MCache(clock))


class MaasMock(object):
    """
    Klein routes for the Monitoring API.
    """

    def __init__(self, api_mock, uri_prefix, session_store, name):
        """
        Create a maas region with a given URI prefix (used for generating URIs
        to servers).
        """
        self._api_mock = api_mock
        self._session_store = session_store
        self._name = name

    def _entity_cache_for_tenant(self, tenant_id):
        """
        Retrieve the M_cache object containing all objects created so far
        """
        clock = self._session_store.clock
        return (self._session_store.session_for_tenant_id(tenant_id)
                .data_for_api(self._api_mock, _mcache_factory(clock))[self._name]
                )

    def _audit(self, app, request, tenant_id, status, content=b''):
        headers = {k.decode("utf-8"): [vv.decode("utf-8") if isinstance(vv, bytes) else vv for vv in v]
                   for k, v in request.getAllHeaders().items()
                   if k != b'x-auth-token'}

        record = {
            'id': text_type(uuid4()),
            'timestamp': int(1000 * self._session_store.clock.seconds()),
            'headers': headers,
            'url': request.path.decode("utf-8"),
            'app': app,
            'query': parse_and_flatten_qs(request.uri.decode("utf-8")),
            'txnId': text_type(uuid4()),
            'payload': content.decode("utf-8"),
            'method': request.method.decode("utf-8"),
            'account_id': tenant_id,
            'who': '',
            'why': '',
            'statusCode': status
        }
        self._entity_cache_for_tenant(tenant_id).audits_list.append(record)

    app = MimicApp()

    @app.route('/v1.0/<string:tenant_id>/mimic/reset', methods=['GET'])
    def doreset(self, request, tenant_id):
        """
        Reset the session
        """
        self._session_store.session_for_tenant_id(tenant_id)._api_objects = {}
        return "Session has been reset for tenant_id " + tenant_id

    @app.route('/v1.0/<string:tenant_id>/entities', methods=['GET'])
    def list_entities(self, request, tenant_id):
        """
        Replies the entities list call
        """
        entities = list(self._entity_cache_for_tenant(
            tenant_id).entities.values())

        limit = 100
        marker = None
        next_marker = None
        next_href = None
        if b'limit' in request.args:
            limit = int(request.args[b'limit'][0].strip())
        if b'marker' in request.args:
            marker = request.args[b'marker'][0].strip().decode("utf-8")
            for q in range(len(entities)):
                if entities[q].id == marker:
                    entities = entities[q:]
                    break
        try:
            next_marker = entities[limit].id
        except Exception:
            pass
        entities = entities[:limit]

        metadata = {'count': len(entities),
                    'limit': limit,
                    'marker': marker,
                    'next_marker': next_marker,
                    'next_href': next_href}
        request.setResponseCode(200)
        return json.dumps({'metadata': metadata,
                           'values': [entity.to_json() for entity in entities]})

    @app.route('/v1.0/<string:tenant_id>/entities', methods=['POST'])
    def create_entity(self, request, tenant_id):
        """
        Creates a new entity
        """
        content = request.content.read()
        postdata = json.loads(content.decode("utf-8"))
        newentity = create_entity(self._session_store.clock, postdata)
        self._entity_cache_for_tenant(tenant_id).entities[
            newentity.id] = newentity
        status = 201
        request.setResponseCode(status)
        request.setHeader(b'location', base_uri_from_request(request).rstrip('/').encode('utf-8') +
                          request.path + b'/' + newentity.id.encode('utf-8'))
        request.setHeader(b'x-object-id', newentity.id.encode('utf-8'))
        request.setHeader(b'content-type', b'text/plain')
        self._audit('entities', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>', methods=['GET'])
    def get_entity(self, request, tenant_id, entity_id):
        """
        Fetches a specific entity
        """
        return _map_getter(self._entity_cache_for_tenant(tenant_id).entities,
                           request,
                           "Entity",
                           entity_id)

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks', methods=['GET'])
    def get_checks_for_entity(self, request, tenant_id, entity_id):
        """
        Returns all the checks for a paricular entity
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            entity = _get_parent_entity(entities, entity_id)
            checks = entity.list_checks()
            metadata = {'count': len(checks),
                        'limit': 1000,
                        'marker': None,
                        'next_marker': None,
                        'next_href': None}
            request.setResponseCode(200)
            return json.dumps({'metadata': metadata, 'values': checks})
        except ParentDoesNotExist as e:
            request.setResponseCode(e.code)
            return json.dumps(e.to_json())

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>', methods=['PUT'])
    def update_entity(self, request, tenant_id, entity_id):
        """
        Update entity in place.
        """
        content = request.content.read()
        update = json.loads(content.decode("utf-8"))
        update_kwargs = dict(update)
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            entity = _get_entity(entities, entity_id)
            entity.update(clock=self._session_store.clock, **update_kwargs)
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            self._audit('entities', request, tenant_id, e.code, content)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        request.setHeader(b'location', base_uri_from_request(request).rstrip('/').encode('utf-8') +
                          request.path)
        request.setHeader(b'x-object-id', entity_id.encode('utf-8'))
        request.setHeader(b'content-type', b'text/plain')
        self._audit('entities', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>', methods=['DELETE'])
    def delete_entity(self, request, tenant_id, entity_id):
        """
        Delete an entity, all checks that belong to entity, all alarms that belong to those checks
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            _delete_entity(entities, entity_id)
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            self._audit('entities', request, tenant_id, e.code)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        request.setHeader(b'content-type', b'text/plain')
        self._audit('entities', request, tenant_id, status)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks', methods=['POST'])
    def create_check(self, request, tenant_id, entity_id):
        """
        Create a check
        """
        content = request.content.read()
        postdata = json.loads(content.decode("utf-8"))
        entities = self._entity_cache_for_tenant(tenant_id).entities

        newcheck = None
        try:
            newcheck = create_check(self._session_store.clock, postdata)
        except TypeError:
            missing_key = _find_missing_required_key(
                Check, postdata, ['created_at', 'updated_at'])
            status = 400
            request.setResponseCode(status)
            self._audit('checks', request, tenant_id, status, content)
            return json.dumps({'type': 'badRequest',
                               'code': status,
                               'message': 'Validation error for key \'{0}\''.format(missing_key),
                               'details': 'Missing required key ({0})'.format(missing_key),
                               'txnId': '.fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf'})

        try:
            entity = _get_entity(entities, entity_id)
            entity.checks[newcheck.id] = newcheck
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            self._audit('checks', request, tenant_id, e.code, content)
            return json.dumps(e.to_json())

        status = 201
        request.setResponseCode(status)
        request.setHeader(b'location', base_uri_from_request(request).rstrip('/').encode('utf-8') +
                          request.path + b'/' + newcheck.id.encode('utf-8'))
        request.setHeader(b'x-object-id', newcheck.id.encode('utf-8'))
        request.setHeader(b'content-type', b'text/plain')
        self._audit('checks', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks/<string:check_id>',
               methods=['GET'])
    def get_check(self, request, tenant_id, entity_id, check_id):
        """
        Get a specific check that was created before
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            check = _get_check(entities, entity_id, check_id)
            return json.dumps(check.to_json())
        except (ObjectDoesNotExist, ParentDoesNotExist) as e:
            request.setResponseCode(e.code)
            return json.dumps(e.to_json())

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks/<string:check_id>',
               methods=['PUT'])
    def update_check(self, request, tenant_id, entity_id, check_id):
        """
        Updates a check in place.
        """
        content = request.content.read()
        update = json.loads(content.decode("utf-8"))
        update_kwargs = dict(update)
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            check = _get_check(entities, entity_id, check_id)
            check.update(clock=self._session_store.clock, **update_kwargs)
        except (ObjectDoesNotExist, ParentDoesNotExist) as e:
            request.setResponseCode(e.code)
            self._audit('checks', request, tenant_id, e.code, content)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        request.setHeader(b'location', base_uri_from_request(request).rstrip('/').encode('utf-8') +
                          request.path)
        request.setHeader(b'x-object-id', check_id.encode('utf-8'))
        request.setHeader(b'content-type', b'text/plain')
        self._audit('checks', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks/<string:check_id>',
               methods=['DELETE'])
    def delete_check(self, request, tenant_id, entity_id, check_id):
        """
        Deletes check and all alarms associated to it
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            _delete_check(entities, entity_id, check_id)
        except (ObjectDoesNotExist, ParentDoesNotExist) as e:
            request.setResponseCode(e.code)
            self._audit('checks', request, tenant_id, e.code)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        request.setHeader(b'content-type', b'text/plain')
        self._audit('checks', request, tenant_id, status)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/test-check', methods=['POST'])
    def test_check(self, request, tenant_id, entity_id):
        """
        Tests a check.

        If the user has configured overrides using the control API for
        test-check using this entity and check type, those will be used.
        Otherwise, random values within each metric type will be
        generated. For instance, integer metrics generate integers, and
        string metrics generate strings. No other guarantees are made.
        """
        content = request.content.read()
        test_config = json.loads(content.decode("utf-8"))
        check_type = test_config['type']
        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store
        response_code, response_body = maas_store.check_types[check_type].get_test_check_response(
            entity_id=entity_id,
            monitoring_zones=test_config.get('monitoring_zones_poll'),
            timestamp=int(1000 * self._session_store.clock.seconds()))
        request.setResponseCode(response_code)
        self._audit('checks', request, tenant_id, response_code, content)
        return json.dumps(response_body)

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms', methods=['POST'])
    def create_alarm(self, request, tenant_id, entity_id):
        """
        Creates alarm
        """
        content = request.content.read()
        postdata = json.loads(content.decode("utf-8"))
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            newalarm = create_alarm(
                self._session_store.clock, entity_id, postdata)
        except TypeError:
            missing_key = _find_missing_required_key(Alarm, postdata, ['created_at',
                                                                       'updated_at',
                                                                       'entity_id'])
            status = 400
            request.setResponseCode(status)
            self._audit('alarms', request, tenant_id, status, content)
            return json.dumps({'type': 'badRequest',
                               'code': status,
                               'message': 'Validation error for key \'{0}\''.format(missing_key),
                               'details': 'Missing required key ({0})'.format(missing_key),
                               'txnId': '.fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf'})

        try:
            entity = _get_parent_entity(entities, entity_id)
            entity.alarms[newalarm.id] = newalarm
        except ParentDoesNotExist as e:
            request.setResponseCode(e.code)
            self._audit('alarms', request, tenant_id, e.code, content)
            return json.dumps(e.to_json())

        status = 201
        request.setResponseCode(status)
        request.setHeader(b'location', base_uri_from_request(request).rstrip('/').encode('utf-8') +
                          request.path + b'/' + newalarm.id.encode('utf-8'))
        request.setHeader(b'x-object-id', newalarm.id.encode('utf-8'))
        request.setHeader(b'content-type', b'text/plain')
        self._audit('alarms', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms/<string:alarm_id>',
               methods=['GET'])
    def get_alarm(self, request, tenant_id, entity_id, alarm_id):
        """
        Gets an alarm by ID.
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            alarm = _get_alarm(entities, entity_id, alarm_id)
            return json.dumps(alarm.to_json())
        except (ObjectDoesNotExist, ParentDoesNotExist) as e:
            request.setResponseCode(e.code)
            return json.dumps(e.to_json())

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms/<string:alarm_id>',
               methods=['PUT'])
    def update_alarm(self, request, tenant_id, entity_id, alarm_id):
        """
        Updates an alarm in place.

        Documentation for this API can be found in the Rackspace Cloud
        Monitoring Developer Guide, section 5.12.5, "Update alarm by ID".
        The full link is quite long, but you can reach it by browsing
        to the following goo.gl URL:

            http://goo.gl/NhxgTZ
        """
        content = request.content.read()
        update = json.loads(content.decode("utf-8"))
        update_kwargs = dict(update)
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            alarm = _get_alarm(entities, entity_id, alarm_id)
            alarm.update(clock=self._session_store.clock, **update_kwargs)
        except (ObjectDoesNotExist, ParentDoesNotExist) as e:
            request.setResponseCode(e.code)
            self._audit('alarms', request, tenant_id, e.code, content)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        request.setHeader(b'location', base_uri_from_request(request).rstrip('/').encode('utf-8') +
                          request.path)
        request.setHeader(b'x-object-id', alarm_id.encode('utf-8'))
        request.setHeader(b'content-type', b'text/plain')
        self._audit('alarms', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms/<string:alarm_id>',
               methods=['DELETE'])
    def delete_alarm(self, request, tenant_id, entity_id, alarm_id):
        """
        Delete an alarm
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            _delete_alarm(entities, entity_id, alarm_id)
        except (ObjectDoesNotExist, ParentDoesNotExist) as e:
            request.setResponseCode(e.code)
            self._audit('alarms', request, tenant_id, e.code)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        self._audit('alarms', request, tenant_id, status)
        request.setHeader(b'content-type', b'text/plain')
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/test-alarm', methods=['POST'])
    def test_alarm(self, request, tenant_id, entity_id):
        """
        Test an alarm.

        This API can be driven using the control API to set an error
        or canned success response. If no error or success response is set,
        it will return success with a random state and status. Users should
        not expect this API to consistently return either OK, WARNING or
        CRITICAL without first setting the response in the control API.
        """
        content = request.content.read()
        payload = json.loads(content.decode("utf-8"))
        n_tests = len(payload['check_data'])
        current_time_milliseconds = int(
            1000 * self._session_store.clock.seconds())
        status = 200
        response_payload = []

        test_responses = self._entity_cache_for_tenant(
            tenant_id).test_alarm_responses
        test_errors = self._entity_cache_for_tenant(
            tenant_id).test_alarm_errors

        if entity_id in test_errors and len(test_errors[entity_id]) > 0:
            error_response = test_errors[entity_id].popleft()
            status = error_response['code']
            response_payload = error_response['response']
        elif entity_id in test_responses:
            n_responses = len(test_responses[entity_id])
            for i in range(n_tests):
                test_response = test_responses[entity_id][i % n_responses]
                response_payload.append({'state': test_response['state'],
                                         'status': test_response.get(
                                             'status', 'Matched default return statement'),
                                         'timestamp': current_time_milliseconds})
        else:
            for _ in range(n_tests):
                response_payload.append({'state': random.choice(['OK', 'WARNING', 'CRITICAL']),
                                         'status': random_hipsum(12),
                                         'timestamp': current_time_milliseconds})

        request.setResponseCode(status)
        self._audit('alarms', request, tenant_id, status, content)
        return json.dumps(response_payload)

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms', methods=['GET'])
    def get_alarms_for_entity(self, request, tenant_id, entity_id):
        """
        Get all alarms for the specified entity.
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities

        try:
            entity = _get_parent_entity(entities, entity_id)
            alarms = entity.list_alarms()
            metadata = {'count': len(alarms),
                        'limit': 1000,
                        'marker': None,
                        'next_marker': None,
                        'next_href': None}
            request.setResponseCode(200)
            return json.dumps({'metadata': metadata, 'values': alarms})
        except ParentDoesNotExist as e:
            request.setResponseCode(e.code)
            return json.dumps(e.to_json())

    @app.route('/v1.0/<string:tenant_id>/views/overview', methods=['GET'])
    def overview(self, request, tenant_id):
        """
        serves the overview api call,returns all entities,checks and alarms
        """
        entity_map = self._entity_cache_for_tenant(tenant_id).entities
        all_entities = None
        if b'entityId' in request.args:
            entity_ids = [a.decode("utf-8") for a in request.args[b'entityId']]
            all_entities = [entity_map[entity_id] for entity_id in entity_ids
                            if entity_id in entity_map]
            if len(all_entities) == 0:
                err = ObjectDoesNotExist(
                    object_type='Entity', key=','.join(entity_ids))
                request.setResponseCode(err.code)
                return json.dumps(err.to_json())
        else:
            all_entities = list(entity_map.values())

        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store
        page_limit = min(int(request.args.get(b'limit', [100])[0]), 1000)
        offset = 0
        current_marker = request.args.get(b'marker', [None])[0]
        if current_marker is not None:
            current_marker = current_marker.decode("utf-8")
            try:
                offset = all_entities.index(
                    Matcher(lambda entity: entity.id == current_marker))
            except ValueError:
                offset = 0

        entities = all_entities[offset:offset + page_limit]
        next_marker = None
        if offset + page_limit < len(all_entities):
            next_marker = all_entities[offset + page_limit].id

        metadata = {
            'count': len(entities),
            'marker': current_marker,
            'next_marker': next_marker,
            'limit': page_limit,
            'next_href': None
        }
        values = [{'alarms': entity.list_alarms(),
                   'checks': entity.list_checks(),
                   'entity': entity.to_json(),
                   'latest_alarm_states': [
                       state.brief_json()
                       for state in maas_store.latest_alarm_states_for_entity(entity.id)]}

                  for entity in entities]
        request.setResponseCode(200)
        return json.dumps({'metadata': metadata, 'values': values})

    @app.route('/v1.0/<string:tenant_id>/audits', methods=['GET'])
    def list_audits(self, request, tenant_id):
        """
        Gets the user's audit logs.
        """
        ordering = -1 if request.args.get(b'reverse', False) else 1
        all_audits = self._entity_cache_for_tenant(
            tenant_id).audits_list[::ordering]
        page_limit = min(int(request.args.get(b'limit', [100])[0]), 1000)
        offset = 0
        current_marker = request.args.get(b'marker', [None])[0]
        if current_marker is not None:
            current_marker = current_marker.decode("utf-8")
            try:
                offset = all_audits.index(
                    Matcher(lambda audit: audit['id'] == current_marker))
            except ValueError:
                offset = 0

        audits = all_audits[offset:offset + page_limit]
        next_marker = None
        if offset + page_limit < len(all_audits):
            next_marker = all_audits[offset + page_limit]['id']

        metadata = {
            'count': len(audits),
            'marker': current_marker,
            'next_marker': next_marker,
            'limit': page_limit,
            'next_href': None
        }
        request.setResponseCode(200)
        return json.dumps({'metadata': metadata, 'values': audits})

    @app.route('/v1.0/<string:tenant_id>/__experiments/json_home', methods=['GET'])
    def service_json_home(self, request, tenant_id):
        """
        jsonhome call. CloudIntellgiences doesn't actually use these URLs directly.
        Rather, do some regex on them to figure how to know what permissions the user as
        have
        TO DO: Regionless api
        """
        request.setResponseCode(200)
        mockapi_id = re.findall('/mimicking/(.+?)/',
                                request.path.decode("utf-8"))[0]
        url = base_uri_from_request(request).rstrip(
            '/') + '/mimicking/' + mockapi_id + '/ORD/v1.0'
        return json.dumps(json_home(url))

    @app.route('/v1.0/<string:tenant_id>/views/agent_host_info', methods=['GET'])
    def view_agent_host_info(self, request, tenant_id):
        """
        Mocks the /views/agent_host_info API call.
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities
        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store

        if b'include' not in request.args:
            request.setResponseCode(400)
            return json.dumps({'type': 'badRequest',
                               'code': 400,
                               'message': 'Validation error for key \'include\'',
                               'details': 'Must include at least one HOST_INFO_TYPE.',
                               'txnId': ('.fake.mimic.transaction.id.c-1111111'
                                          '.ts-123444444.v-12344frf')})

        if b'entityId' not in request.args:
            request.setResponseCode(400)
            return json.dumps({'type': 'badRequest',
                               'code': 400,
                               'message': 'Validation error for key \'agentId, entityId, uri\'',
                               'details': 'You must specify an agentId, entityId, or an entity URI.',
                               'mimicNotes': 'But mimic will only accept entityId right now',
                               'txnId': ('.fake.mimic.transaction.id.c-1111111'
                                         '.ts-123444444.v-12344frf')})

        entity_id = request.args[b'entityId'][0].strip().decode("utf-8")
        entity = None

        try:
            entity = _get_entity(entities, entity_id)
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            return json.dumps(e.to_json())

        if entity.agent_id is None:
            request.setResponseCode(400)
            return json.dumps({'type': 'agentDoesNotExist',
                               'code': 400,
                               'message': 'Agent does not exist',
                               'details': 'Agent null does not exist',
                               'txnId': ('.fake.mimic.transaction.id.c-1111111.'
                                         'ts-123444444.v-12344frf')})

        try:
            agent = maas_store.agents[entity.agent_id]
        except KeyError:
            request.setResponseCode(400)
            return json.dumps({'type': 'agentDoesNotExist',
                               'code': 400,
                               'message': 'Agent does not exist',
                               'details': 'Agent {0} does not exist'.format(entity.agent_id),
                               'txnId': ('.fake.mimic.transaction.id.c-1111111.'
                                         'ts-123444444.v-12344frf')})

        request.setResponseCode(200)
        return json.dumps({
            'values': [{'agent_id': entity.agent_id,
                        'entity_id': entity_id,
                        'entity_uri': entity.uri,
                        'host_info': agent.get_host_info(
                            maas_store.host_info_types,
                            [arg.decode('utf-8')
                             for arg in request.args[b'include']],
                            entity_id,
                            self._session_store.clock)}],
            'metadata': {'count': 1,
                         'limit': 100,
                         'marker': None,
                         'next_marker': None,
                         'next_href': None}})

    @app.route('/v1.0/<string:tenant_id>/views/connections', methods=['GET'])
    def view_connections(self, request, tenant_id):
        """
        Lists agent connections.
        """
        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store

        if b'agentId' not in request.args:
            request.setResponseCode(400)
            return json.dumps({'type': 'badRequest',
                               'code': 400,
                               'message': 'Validation error for key \'agentId\'',
                               'details': 'You must specify an agentId',
                               'txnId': '.fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf'})

        agent_ids = request.args[b'agentId']
        decoded_agent_ids = [agent_id.decode(
            "utf-8") for agent_id in agent_ids]
        connections = [{'agent_id': agent_id,
                        'connections': [connection.to_json()
                                        for connection in maas_store.list_connections_for_agent(
                                            agent_id)]}
                       for agent_id in decoded_agent_ids]
        return json.dumps({'values': connections,
                           'metadata': {'count': len(connections),
                                        'limit': None,
                                        'marker': None,
                                        'next_marker': None,
                                        'next_href': None}})

    @app.route('/v1.0/<string:tenant_id>/agent_installers', methods=['POST'])
    def agent_installer(self, request, tenant_id):
        """
        URL of agent install script
        """
        xsil = (b'https://monitoring.api.rackspacecloud.com'
                b'/v1.0/00000/agent_installers/c69b2ceafc0444506fb32255af3d9be3.sh')
        status = 201
        request.setResponseCode(status)
        request.setHeader(b'x-shell-installer-location', xsil)
        self._audit('agent_installers', request, tenant_id,
                    status, request.content.read())
        return b''

    @app.route('/v1.0/<string:tenant_id>/notifications', methods=['POST'])
    def create_notification(self, request, tenant_id):
        """
        Create notification target
        """
        content = request.content.read()
        new_n = create_notification(
            self._session_store.clock, json.loads(content.decode("utf-8")))
        notifications = self._entity_cache_for_tenant(tenant_id).notifications
        notifications[new_n.id] = new_n
        status = 201
        request.setResponseCode(status)
        request.setHeader(b'content-type', b'text/plain')
        request.setHeader(b'location', base_uri_from_request(request).rstrip('/').encode('utf-8') +
                          request.path + b'/' + new_n.id.encode('utf-8'))
        request.setHeader(b'x-object-id', new_n.id.encode('utf-8'))
        self._audit('notifications', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/notifications', methods=['GET'])
    def get_notifications(self, request, tenant_id):
        """
        Get notification targets
        """
        notifications = self._entity_cache_for_tenant(tenant_id).notifications
        metadata = {'count': len(notifications),
                    'limit': 100,
                    'marker': None,
                    'next_marker': None,
                    'next_href': None}
        request.setResponseCode(200)
        return json.dumps({'values': [nt.to_json() for nt in notifications.values()],
                           'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/notifications/<string:nt_id>', methods=['PUT'])
    def update_notifications(self, request, tenant_id, nt_id):
        """
        Updates notification targets
        """
        content = request.content.read()
        postdata = json.loads(content.decode("utf-8"))
        update_kwargs = dict(postdata)
        notifications = self._entity_cache_for_tenant(tenant_id).notifications

        try:
            notification = _get_notification(notifications, nt_id)
            notification.update(
                clock=self._session_store.clock, **update_kwargs)
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            self._audit('notifications', request, tenant_id, e.code, content)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        request.setHeader(b'content-type', b'text/plain')
        self._audit('notifications', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/notifications/<string:nt_id>', methods=['DELETE'])
    def delete_notification(self, request, tenant_id, nt_id):
        """
        Delete a notification
        """
        notifications = self._entity_cache_for_tenant(tenant_id).notifications

        try:
            _delete_notification(notifications, nt_id)
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            self._audit('notifications', request, tenant_id, e.code)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        self._audit('notifications', request, tenant_id, status)
        request.setHeader(b'content-type', b'text/plain')
        return b''

    @app.route('/v1.0/<string:tenant_id>/notification_plans', methods=['POST'])
    def create_notificationplan(self, request, tenant_id):
        """
        Creates a new notificationPlans
        """
        content = request.content.read()
        postdata = json.loads(content.decode("utf-8"))
        notification_plans = self._entity_cache_for_tenant(
            tenant_id).notification_plans
        newnp = create_notification_plan(self._session_store.clock, postdata)
        notification_plans[newnp.id] = newnp
        status = 201
        request.setResponseCode(status)
        request.setHeader(b'content-type', b'text/plain')
        request.setHeader(b'location', base_uri_from_request(request).rstrip('/').encode('utf-8') +
                          request.path + b'/' + newnp.id.encode('utf-8'))
        request.setHeader(b'x-object-id', newnp.id.encode('utf-8'))
        self._audit('notification_plans', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/notification_plans', methods=['GET'])
    def get_notification_plans(self, request, tenant_id):
        """
        Get all notification plans
        """
        np_list = self._entity_cache_for_tenant(
            tenant_id).notification_plans.values()
        metadata = {'count': len(np_list),
                    'limit': 100,
                    'marker': None,
                    'next_marker': None,
                    'next_href': None}
        request.setResponseCode(200)
        return json.dumps({'values': [np.to_json() for np in np_list], 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/notification_plans/<string:np_id>', methods=['GET'])
    def get_notification_plan(self, request, tenant_id, np_id):
        """
        Get specific notif plan
        """
        notification_plans = self._entity_cache_for_tenant(
            tenant_id).notification_plans
        return _map_getter(notification_plans, request, 'NotificationPlan', np_id)

    @app.route('/v1.0/<string:tenant_id>/notification_plans/<string:np_id>', methods=['PUT'])
    def update_notification_plan(self, request, tenant_id, np_id):
        """
        Alter a notification plan
        """
        content = request.content.read()
        postdata = json.loads(content.decode("utf-8"))
        update_kwargs = dict(postdata)
        notification_plans = self._entity_cache_for_tenant(
            tenant_id).notification_plans

        try:
            notification_plan = _get_notification_plan(
                notification_plans, np_id)
            notification_plan.update(
                clock=self._session_store.clock, **update_kwargs)
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            self._audit('notification_plans', request,
                        tenant_id, e.code, content)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        request.setHeader(b'content-type', b'text/plain')
        self._audit('notification_plans', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/notification_plans/<string:np_id>', methods=['DELETE'])
    def delete_notification_plan(self, request, tenant_id, np_id):
        """
        Remove a notification plan
        """
        notification_plans = self._entity_cache_for_tenant(
            tenant_id).notification_plans
        entities = self._entity_cache_for_tenant(tenant_id).entities
        alarmids_using_np = [alarm.id
                             for entity in entities.values()
                             for alarm in entity.alarms.values()
                             if alarm.notification_plan_id == np_id]

        if len(alarmids_using_np):
            status = 403
            request.setResponseCode(status)
            err_message = ('Notification plans cannot be removed while alarms ' +
                           'are using it: {0}'.format(' '.join(alarmids_using_np)))
            self._audit('notification_plans', request, tenant_id, status)
            return json.dumps({'type': 'forbiddenError',
                               'code': status,
                               'txnId': '.fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf',
                               'message': err_message,
                               'details': err_message})

        try:
            _delete_notification_plan(notification_plans, np_id)
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            self._audit('notification_plans', request, tenant_id, e.code)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        self._audit('notification_plans', request, tenant_id, status)
        request.setHeader(b'content-type', b'text/plain')
        return b''

    @app.route('/v1.0/<string:tenant_id>/suppressions', methods=['GET'])
    def get_suppressions(self, request, tenant_id):
        """
        Get the list of suppressions for this tenant.
        """
        sp_list = self._entity_cache_for_tenant(
            tenant_id).suppressions.values()
        metadata = {
            'count': len(sp_list),
            'limit': 100,
            'marker': None,
            'next_marker': None,
            'next_href': None
        }
        request.setResponseCode(200)
        return json.dumps({'values': [sp.to_json() for sp in sp_list], 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/suppressions/<string:sp_id>', methods=['GET'])
    def get_suppression(self, request, tenant_id, sp_id):
        """
        Get a suppression by ID.
        """
        suppressions = self._entity_cache_for_tenant(tenant_id).suppressions
        return _map_getter(suppressions, request, 'Suppression', sp_id)

    @app.route('/v1.0/<string:tenant_id>/suppressions', methods=['POST'])
    def create_suppression(self, request, tenant_id):
        """
        Create a new suppression.
        """
        content = request.content.read()
        postdata = json.loads(content.decode("utf-8"))
        newsp = create_suppression(self._session_store.clock, postdata)
        suppressions = self._entity_cache_for_tenant(tenant_id).suppressions
        suppressions[newsp.id] = newsp
        status = 201
        request.setResponseCode(status)
        request.setHeader(b'location', base_uri_from_request(request).rstrip('/').encode('utf-8') +
                          request.path + b'/' + newsp.id.encode('utf-8'))
        request.setHeader(b'x-object-id', newsp.id.encode('utf-8'))
        request.setHeader(b'content-type', b'text/plain')
        self._audit('suppressions', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/suppressions/<string:sp_id>', methods=['PUT'])
    def update_suppression(self, request, tenant_id, sp_id):
        """
        Update a suppression.
        """
        content = request.content.read()
        postdata = json.loads(content.decode("utf-8"))
        update_kwargs = dict(postdata)
        suppressions = self._entity_cache_for_tenant(tenant_id).suppressions

        try:
            suppression = _get_suppression(suppressions, sp_id)
            suppression.update(
                clock=self._session_store.clock, **update_kwargs)
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            self._audit('suppressions', request, tenant_id, e.code, content)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        request.setHeader(b'content-type', b'text/plain')
        self._audit('suppressions', request, tenant_id, status, content)
        return b''

    @app.route('/v1.0/<string:tenant_id>/suppressions/<string:sp_id>', methods=['DELETE'])
    def delete_suppression(self, request, tenant_id, sp_id):
        """
        Delete a suppression.
        """
        suppressions = self._entity_cache_for_tenant(tenant_id).suppressions

        try:
            _delete_suppression(suppressions, sp_id)
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            self._audit('suppressions', request, tenant_id, e.code)
            return json.dumps(e.to_json())

        status = 204
        request.setResponseCode(status)
        self._audit('suppressions', request, tenant_id, status)
        request.setHeader(b'content-type', b'text/plain')
        return b''

    @app.route('/v1.0/<string:tenant_id>/monitoring_zones', methods=['GET'])
    def list_monitoring_zones(self, request, tenant_id):
        """
        Lists the monitoring zones
        """
        mzs = monitoring_zones()
        metadata = {
            'count': len(mzs),
            'limit': 100,
            'marker': None,
            'next_marker': None,
            'next_href': None
        }
        request.setResponseCode(200)
        return json.dumps({'values': mzs, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/alarm_examples', methods=['GET'])
    def list_alarm_examples(self, request, tenant_id):
        """
        Lists all of the alarm examples.
        """
        axs = alarm_examples()
        metadata = {
            'count': len(axs),
            'limit': 100,
            'marker': None,
            'next_marker': None,
            'next_href': None
        }
        request.setResponseCode(200)
        return json.dumps({'values': axs, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/views/alarmCountsPerNp', methods=['GET'])
    def alarm_counts_per_np(self, request, tenant_id):
        """
        All NotificationPlans a number of alarms pointing to them.
        """
        notification_plans = self._entity_cache_for_tenant(
            tenant_id).notification_plans
        entities = self._entity_cache_for_tenant(tenant_id).entities

        values = [{'notification_plan_id': np.id,
                   'alarm_count': len([alarm
                                       for entity in entities.values()
                                       for alarm in entity.alarms.values()
                                       if alarm.notification_plan_id == np.id])}
                  for np in notification_plans.values()]

        metadata = {'limit': 100,
                    'marker': None,
                    'next_marker': None,
                    'next_href': None,
                    'count': len(values)}
        request.setResponseCode(200)
        return json.dumps({'values': values, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/views/alarmsByNp/<string:np_id>', methods=['GET'])
    def alarms_by_np(self, request, tenant_id, np_id):
        """
        List of alarms pointing to a particular NotificationPlan
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities
        values = [alarm.to_json()
                  for entity in entities.values()
                  for alarm in entity.alarms.values()
                  if alarm.notification_plan_id == np_id]
        metadata = {'limit': 100,
                    'marker': None,
                    'next_marker': None,
                    'next_href': None,
                    'count': len(values)}
        request.setResponseCode(200)
        return json.dumps({'values': values, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/notification_types', methods=['GET'])
    def get_notification_types(self, request, tenant_id):
        """
        Get the types of notifications supported: pageduty,email,sms, etc
        """
        ntlist = self._entity_cache_for_tenant(
            tenant_id).notificationtypes_list
        metadata = {'count': len(ntlist),
                    'limit': 100,
                    'marker': None,
                    'next_marker': None,
                    'next_href': None}
        request.setResponseCode(200)
        return json.dumps({'values': ntlist, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/views/metric_list', methods=['GET'])
    def views_metric_list(self, request, tenant_id):
        """
        All available metrics.
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities
        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store
        values = [_metric_list_for_entity(maas_store, entity)
                  for entity in entities.values()]

        metadata = {'count': len(values),
                    'marker': None,
                    'next_marker': None,
                    'limit': 1000,
                    'next_href': None}

        request.setResponseCode(200)
        return json.dumps({'metadata': metadata, 'values': values})

    @app.route('/v1.0/<string:tenant_id>/__experiments/multiplot', methods=['POST'])
    def multiplot(self, request, tenant_id):
        """
        datapoints for all metrics requested
        Right now, only checks of type remote.ping work
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities
        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store
        content = request.content.read()
        multiplot_request = json.loads(content.decode("utf-8"))

        requested_check_ids = set([metric['check_id']
                                   for metric in multiplot_request['metrics']])
        checks_by_id = {check.id: check
                        for entity in entities.values()
                        for check in entity.checks.values()
                        if check.id in requested_check_ids}

        for requested_metric in multiplot_request['metrics']:
            if requested_metric['check_id'] not in checks_by_id:
                status = 400
                request.setResponseCode(status)
                self._audit('rollups', request, tenant_id, status, content)
                return json.dumps({
                    'type': 'requiredNotFoundError',
                    'code': status,
                    'message': 'Required object does not exist',
                    'details': 'Object "Check" with key "{0},{1}" does not exist'.format(
                        requested_metric['entity_id'], requested_metric['check_id']),
                    'txnId': '.fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf'})

        multiplot_metrics = [_compute_multiplot(maas_store,
                                                metric['entity_id'],
                                                checks_by_id[
                                                    metric['check_id']],
                                                metric['metric'],
                                                int(request.args[b'from'][0]),
                                                int(request.args[b'to'][0]),
                                                int(request.args[b'points'][0]))
                             for metric in multiplot_request['metrics']]
        status = 200
        request.setResponseCode(200)
        self._audit('rollups', request, tenant_id, status, content)
        return json.dumps({'metrics': multiplot_metrics})

    @app.route('/v1.0/<string:tenant_id>/views/latest_alarm_states', methods=['GET'])
    def latest_alarm_states(self, request, tenant_id):
        """
        Gets entities grouped with their latest alarm states.
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities
        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store

        values = [{'entity_id': entity.id,
                   'entity_uri': entity.uri,
                   'entity_label': entity.label,
                   'latest_alarm_states': [
                       state.detail_json()
                       for state in maas_store.latest_alarm_states_for_entity(entity.id)]}
                  for entity in entities.values()]

        metadata = {'count': len(values),
                    'marker': None,
                    'next_marker': None,
                    'limit': 1000,
                    'next_href': None}

        request.setResponseCode(200)
        return json.dumps({'values': values, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/changelogs/alarms', methods=['GET'])
    def change_logs(self, request, tenant_id):
        """
        Gets entities, checks and alarms grouped with their latest alarm states.
        """
        all_alarm_states = self._entity_cache_for_tenant(
            tenant_id).maas_store.alarm_states

        values = [{'id': text_type(uuid4()),  # probably "correct" would be each_alarm_state.id
                   'timestamp': int(1000 * self._session_store.clock.seconds()),
                   'entity_id': each_alarm_state.entity_id,
                   'alarm_id': each_alarm_state.alarm_id,
                   'check_id': each_alarm_state.check_id,
                   'status': each_alarm_state.status,
                   'state': each_alarm_state.state,
                   'previous_state': each_alarm_state.previous_state,
                   'observation': each_alarm_state.status,
                   'analyzed_by_monitoring_zone_id': each_alarm_state.analyzed_by_monitoring_zone_id}
                  for each_alarm_state in all_alarm_states]
        metadata = {'count': len(values),
                    'marker': None,
                    'next_marker': None,
                    'limit': 1000,
                    'next_href': None}

        request.setResponseCode(200)
        return json.dumps({'values': values, 'metadata': metadata})


@implementer(IAPIMock, IPlugin)
@attr.s
class MaasControlApi(object):
    """
    This class registers the MaaS controller API in the service catalog.
    """
    maas_api = attr.ib()

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the MaaS API.
        """
        return [
            Entry(
                tenant_id, "rax:monitor", "cloudMonitoringControl",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()),
                             "v1.0")
                    for region in self.maas_api._regions
                ]
            )
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        maas_controller = MaasController(api_mock=self,
                                         session_store=session_store,
                                         region=region)
        return maas_controller.app.resource()


@attr.s
class MaasController(object):
    """
    Klein routes for MaaS control API.
    """
    api_mock = attr.ib()
    session_store = attr.ib()
    region = attr.ib()

    def _entity_cache_for_tenant(self, tenant_id):
        """
        Retrieve the M_cache object containing all objects created so far
        """
        clock = self.session_store.clock
        return (self.session_store.session_for_tenant_id(tenant_id)
                .data_for_api(self.api_mock.maas_api, _mcache_factory(clock))[self.region])

    app = MimicApp()

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms/test_response',
               methods=['PUT'])
    def set_test_alarm_response(self, request, tenant_id, entity_id):
        """
        Sets the test-alarm response for a given entity.
        """
        test_responses = self._entity_cache_for_tenant(
            tenant_id).test_alarm_responses
        dummy_response = json_from_request(request)
        test_responses[entity_id] = []
        for response_block in dummy_response:
            ith_response = {'state': response_block['state']}
            if 'status' in response_block:
                ith_response['status'] = response_block['status']
            test_responses[entity_id].append(ith_response)
        request.setResponseCode(204)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms/test_errors',
               methods=['POST'])
    def push_test_alarm_error(self, request, tenant_id, entity_id):
        """
        Creates a new error response that will be returned from the
        test-alarm API the next time it is called for this entity.
        """
        test_alarm_errors = self._entity_cache_for_tenant(
            tenant_id).test_alarm_errors
        request_body = json_from_request(request)

        if entity_id not in test_alarm_errors:
            test_alarm_errors[entity_id] = collections.deque()

        error_obj = {'id': 'er' + random_hex_generator(4),
                     'code': request_body['code'],
                     'response': request_body['response']}
        test_alarm_errors[entity_id].append(error_obj)
        request.setResponseCode(201)
        request.setHeader(b'x-object-id', error_obj['id'].encode('utf-8'))
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms/test_response',
               methods=['DELETE'])
    def clear_test_alarm_response(self, request, tenant_id, entity_id):
        """
        Clears the test-alarm response and restores normal behavior.
        """
        test_responses = self._entity_cache_for_tenant(
            tenant_id).test_alarm_responses
        del test_responses[entity_id]
        request.setResponseCode(204)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks' +
               '/test_responses/<string:check_type>', methods=['PUT'])
    def set_test_check_overrides(self, request, tenant_id, entity_id, check_type):
        """
        Sets overriding behavior on the test-check handler for a given
        entity ID and check type.
        """
        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store
        check_type_ins = maas_store.check_types[check_type]
        overrides = json_from_request(request)
        check_id = '__test_check'
        ench_key = (entity_id, check_id)

        for override in overrides:
            if 'available' in override:
                check_type_ins.test_check_available[
                    ench_key] = override['available']
            if 'status' in override:
                check_type_ins.test_check_status[ench_key] = override['status']
            metrics_dict = override.get('metrics', {})
            for metric_name in metrics_dict:
                test_check_metric = check_type_ins.get_metric_by_name(
                    metric_name)
                kwargs = {'entity_id': entity_id,
                          'check_id': check_id,
                          'override_fn': lambda _: metrics_dict[metric_name]['data']}
                if 'monitoring_zone_id' in override:
                    kwargs['monitoring_zone'] = override['monitoring_zone_id']
                test_check_metric.set_override(**kwargs)

        request.setResponseCode(204)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks' +
               '/test_responses/<string:check_type>', methods=['DELETE'])
    def clear_test_check_overrides(self, request, tenant_id, entity_id, check_type):
        """
        Clears overriding behavior on a test-check handler.
        """
        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store
        check_type_ins = maas_store.check_types[check_type]
        check_type_ins.clear_overrides()
        request.setResponseCode(204)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms' +
               '/<string:alarm_id>/states', methods=['POST'])
    def create_alarm_state(self, request, tenant_id, entity_id, alarm_id):
        """
        Adds a new alarm state to the collection of alarm states.
        """
        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store
        entities = self._entity_cache_for_tenant(tenant_id).entities
        request_body = json_from_request(request)
        alarm = None

        try:
            alarm = _get_alarm(entities, entity_id, alarm_id)
        except (ObjectDoesNotExist, ParentDoesNotExist) as e:
            request.setResponseCode(e.code)
            return json.dumps(e.to_json())

        previous_state = u'UNKNOWN'
        alarm_states_same_entity_and_alarm = [
            state for state in maas_store.alarm_states
            if state.entity_id == entity_id and state.alarm_id == alarm_id]
        if len(alarm_states_same_entity_and_alarm) > 0:
            previous_state = alarm_states_same_entity_and_alarm[-1].state

        monitoring_zone_id = request_body.get(
            'analyzed_by_monitoring_zone_id', u'mzord')

        new_state = None
        try:
            new_state = AlarmState(alarm_id=alarm_id,
                                   entity_id=entity_id,
                                   check_id=alarm.check_id,
                                   alarm_label=alarm.label,
                                   analyzed_by_monitoring_zone_id=monitoring_zone_id,
                                   previous_state=previous_state,
                                   state=request_body['state'],
                                   status=request_body['status'],
                                   timestamp=int(1000 * self.session_store.clock.seconds()))
        except KeyError as e:
            missing_key = e.args[0]
            status = 400
            request.setResponseCode(status)
            return json.dumps({'type': 'badRequest',
                               'code': status,
                               'message': 'Validation error for key \'{0}\''.format(missing_key),
                               'details': 'Missing required key ({0})'.format(missing_key),
                               'txnId': '.fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf'})

        maas_store.alarm_states.append(new_state)
        request.setResponseCode(201)
        request.setHeader(b'x-object-id', new_state.id.encode('utf-8'))
        request.setHeader(b'content-type', b'text/plain')
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks' +
               '/<string:check_id>/metrics/<string:metric_name>', methods=['PUT'])
    def set_metric_override(self, request, tenant_id, entity_id, check_id, metric_name):
        """
        Sets overrides on a metric.
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities
        check = None

        try:
            check = _get_check(entities, entity_id, check_id)
        except (ObjectDoesNotExist, ParentDoesNotExist) as e:
            request.setResponseCode(e.code)
            return json.dumps(e.to_json())

        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store
        metric = maas_store.check_types[
            check.type].get_metric_by_name(metric_name)
        request_body = json_from_request(request)
        monitoring_zones = request_body.get('monitoring_zones', ['__AGENT__'])
        override_type = request_body['type']
        override_options = request_body.get('options', {})
        override_fn = None

        if override_type == 'squarewave':
            fn_period = int(override_options.get('period', 10 * 60 * 1000))
            half_period = fn_period / 2
            fn_min = override_options.get('min', 20)
            fn_max = override_options.get('max', 80)
            fn_offset = int(override_options.get('offset', 0))
            override_fn = (lambda t: (fn_min
                                      if ((t + fn_offset) % fn_period) < half_period
                                      else fn_max))
        else:
            request.setResponseCode(400)
            return json.dumps({'type': 'badRequest',
                               'code': 400,
                               'message': 'Validation error for key \'type\'',
                               'details': 'Unknown value for "type": "{0}"'.format(override_type)})

        for monitoring_zone in monitoring_zones:
            metric.set_override(
                entity_id=entity_id,
                check_id=check_id,
                monitoring_zone=monitoring_zone,
                override_fn=override_fn)
        request.setResponseCode(204)
        return b''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/agents', methods=['POST'])
    def create_agent(self, request, tenant_id, entity_id):
        """
        Creates or overwrites an agent on the entity.
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities
        maas_store = self._entity_cache_for_tenant(tenant_id).maas_store
        agent = None

        try:
            entity = _get_entity(entities, entity_id)
            agent = Agent()
            entity.agent_id = agent.id
        except ObjectDoesNotExist as e:
            request.setResponseCode(e.code)
            return json.dumps(e.to_json())

        maas_store.agents[agent.id] = agent
        request.setResponseCode(201)
        request.setHeader(b'x-object-id', agent.id.encode('utf-8'))
        request.setHeader(b'content-type', b'text/plain')
        return b''
