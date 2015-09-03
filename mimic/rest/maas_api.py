"""
MAAS Mock API
"""

import json
import collections
import urlparse
import random
import re
from uuid import uuid4

from six import text_type

from zope.interface import implementer

from twisted.plugin import IPlugin

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.rest.mimicapp import MimicApp
from mimic.imimic import IAPIMock
from mimic.canned_responses.maas_json_home import json_home
from mimic.canned_responses.maas_agent_info import agent_info
from mimic.canned_responses.maas_monitoring_zones import monitoring_zones
from mimic.canned_responses.maas_alarm_examples import alarm_examples
from mimic.util.helper import random_hex_generator


class _MatchesID(object):
    """
    Class for implementing equality based on the id field.
    """
    def __init__(self, id):
        """
        Set id on self so that other objects can be compared against this one.
        """
        self.id = id

    def __eq__(self, other):
        """
        Implements the == comparison based on the id field (and nothing else).
        """
        return other['id'] == self.id


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
        List catalog entries for the Nova API.
        """
        return [
            Entry(
                tenant_id, "rax: monitor", "cloudMonitoring",
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

        self.agenthostinfo_querycount = collections.defaultdict(lambda: 0, {})
        self.entities_list = []
        self.checks_list = []
        self.alarms_list = []
        self.notifications_list = [{'id': 'ntTechnicalContactsEmail',
                                    'label': 'Email All Technical Contacts',
                                    'created_at': current_time_milliseconds,
                                    'updated_at': current_time_milliseconds,
                                    'metadata': None,
                                    'type': 'technicalContactsEmail',
                                    'details': None}]
        self.notificationplans_list = [{'id': 'npTechnicalContactsEmail',
                                        'label': 'Technical Contacts - Email',
                                        'critical_state': [], 'warning_state': [],
                                        'ok_state': [], 'metadata': None}]
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
        self.suppressions_list = []
        self.audits_list = []


def create_entity(clock, params):
    """
    Returns a dictionary representing an entity

    :return: an Entity model, which is described in `the Rackspace Cloud
        Monitoring Developer Guide, section 5.4
        <http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-entities.html>`_
    :rtype: ``dict`` mapping ``unicode`` to ``unicode``, ``float``,
        ``bool``, ``dict`` or ``NoneType``.
    """
    params = collections.defaultdict(lambda: '', params)
    current_time_milliseconds = int(1000 * clock.seconds())

    newentity = {}
    newentity['label'] = params['label']
    newentity['id'] = 'en' + random_hex_generator(4)
    newentity['agent_id'] = params['agent_id'] or random_hex_generator(12)
    newentity['created_at'] = current_time_milliseconds
    newentity['updated_at'] = current_time_milliseconds
    newentity['managed'] = params['managed'] or False
    newentity['metadata'] = params['metadata']
    newentity['ip_addresses'] = params['ip_addresses'] or {}
    newentity['uri'] = params['uri'] or None
    return newentity


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

    params = collections.defaultdict(lambda: '', params)
    params['id'] = 'ch' + random_hex_generator(4)
    params['collectors'] = []
    for q in range(3):
        params['collectors'].append('co' + random_hex_generator(3))
    params['confd_hash'] = None
    params['confd_name'] = None
    params['created_at'] = current_time_milliseconds
    params['updated_at'] = current_time_milliseconds
    params['timeout'] = 10
    params['period'] = 60
    params['disabled'] = False
    params['metadata'] = None
    params['target_alias'] = None
    if 'count' not in params['details']:
        params['details'] = {'count': 5}  # I have no idea what count=5 is for.
    return params


def create_alarm(clock, params):
    """
    Returns a dictionary representing an alarm

    :return: an Alarm model, which is described in `the Rackspace Cloud
        Monitoring Developer Guide, section 5.12
        <http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-alarms.html>`_
    :rtype: ``dict`` mapping ``unicode`` to ``unicode``, ``float``,
        ``bool``, ``dict``, or ``NoneType``.
    """
    current_time_milliseconds = int(1000 * clock.seconds())

    params = collections.defaultdict(lambda: '', params)
    params['id'] = 'al' + random_hex_generator(4)
    params['confd_hash'] = None
    params['confd_name'] = None
    params['created_at'] = current_time_milliseconds
    params['updated_at'] = current_time_milliseconds
    params['disabled'] = False
    params['metadata'] = None
    return params


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

    params['id'] = 'np' + random_hex_generator(4)
    params['critical_state'] = None
    params['warning_state'] = None
    params['ok_state'] = None
    params['created_at'] = current_time_milliseconds
    params['updated_at'] = current_time_milliseconds
    params['metadata'] = None
    return params


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

    params['id'] = 'nt' + random_hex_generator(4)
    params['created_at'] = current_time_milliseconds
    params['updated_at'] = current_time_milliseconds
    params['metadata'] = None
    return params


def create_suppression(params):
    """
    Creates a suppression

    :return: a Suppression model, which is described in `the Rackspace
        Cloud Monitoring Developer Guide, section 5.16
        <http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-suppressions.html>`_
    :rtype: ``dict`` mapping ``unicode`` to ``unicode`` or ``list``.
    """
    params['id'] = 'sp' + random_hex_generator(4)
    if 'notification_plans' not in params:
        params['notification_plans'] = []
    if 'entities' not in params:
        params['entities'] = []
    if 'checks' not in params:
        params['checks'] = []
    if 'alarms' not in params:
        params['alarms'] = []
    return params


def create_metric_list_from_entity(entity, allchecks):
    """
    To respond to the metrics_list api call, we must have the entity and allchecks
    and assemble the structure to reply with.
    """
    v = {}
    v['entity_id'] = entity['id']
    v['entity_label'] = entity['label']
    v['checks'] = []
    for c in allchecks:
        if c['type'] == 'remote.ping' and c['entity_id'] == entity['id']:
            metricscheck = {}
            metricscheck['id'] = c['id']
            metricscheck['label'] = c['label']
            metricscheck['type'] = 'remote.ping'
            metricscheck['metrics'] = []
            for mz in c['monitoring_zones_poll']:
                metricscheck['metrics'].append(
                    {'name': mz + '.available', 'unit': 'percent', 'type': 'D'})
                metricscheck['metrics'].append(
                    {'name': mz + '.average', 'unit': 'seconds', 'type': 'D'})
            v['checks'].append(metricscheck)
    return v


def create_multiplot_from_metric(metric, reqargs, allchecks):
    """
    Given a metric, this will produce fake datapoints to graph
    This is for the multiplot API call

    Also, if you name a PING check "squarewave", you will get
    datapoints that form such a wave. This is for testing the
    graphing-solution you have in place. Produces a static, yet
    unique-looking, graph for screen comparison solutions.
    """
    fromdate = int(reqargs['from'][0])
    todate = int(reqargs['to'][0])
    points = int(reqargs['points'][0])
    multiplot = {}
    squarewave_downtrend = 1
    for c in allchecks:
        if c['entity_id'] == metric['entity_id']:
            if c['type'] == 'remote.ping':
                multiplot['entity_id'] = metric['entity_id']
                multiplot['check_id'] = metric['check_id']
                multiplot['type'] = 'number'
                multiplot['metric'] = metric['metric']
                if metric['metric'].endswith('available'):
                    multiplot['unit'] = 'percent'
                else:
                    multiplot['unit'] = 'seconds'
                multiplot['data'] = []
                interval = (todate - fromdate) / points
                timestamp = fromdate
                for q in range(points):
                    d = {}
                    d['numPoints'] = 4
                    d['timestamp'] = timestamp
                    if not q % (points / 4):
                        squarewave_downtrend = squarewave_downtrend ^ 1
                    if c['label'] == 'squarewave':
                        if squarewave_downtrend:
                            d['average'] = 15
                        else:
                            d['average'] = 85
                    else:
                        d['average'] = random.randint(1, 99)
                    multiplot['data'].append(d)
                    timestamp += interval

    return multiplot


def parse_and_flatten_qs(url):
    """
    Parses a querystring and flattens 1-arg arrays.
    """
    qs = urlparse.parse_qs(url)
    flat_qs = {}
    for key in qs:
        flat_qs[key] = qs[key][0] if len(qs[key]) == 1 else qs[key]
    return flat_qs


class MaasMock(object):

    """
    Klein routes for the Monitoring API.
    """

    def __init__(self, api_mock, uri_prefix, session_store, name):
        """
        Create a maas region with a given URI prefix (used for generating URIs
        to servers).
        """
        self.endpoint_port = '8900'
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._name = name

    def _entity_cache_for_tenant(self, tenant_id):
        """
        Retrieve the M_cache object containing all objects created so far
        """
        return (self._session_store.session_for_tenant_id(tenant_id)
                .data_for_api(self._api_mock,
                              lambda: collections.defaultdict(
                                  lambda: MCache(self._session_store.clock)))[self._name]
                )

    def _audit(self, app, request, tenant_id, status, content=''):
        headers = dict([(k, v) for k, v in request.getAllHeaders().iteritems()
                        if k != 'x-auth-token'])

        self._entity_cache_for_tenant(tenant_id).audits_list.append(
            {
                'id': str(uuid4()),
                'timestamp': int(1000 * self._session_store.clock.seconds()),
                'headers': headers,
                'url': request.path,
                'app': app,
                'query': parse_and_flatten_qs(request.uri),
                'txnId': str(uuid4()),
                'payload': content,
                'method': request.method,
                'account_id': tenant_id,
                'who': '',
                'why': '',
                'statusCode': status
            })

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
        entities = self._entity_cache_for_tenant(tenant_id).entities_list

        limit = 100
        marker = None
        next_marker = None
        next_href = None
        if 'limit' in request.args:
            limit = int(request.args['limit'][0].strip())
        if 'marker' in request.args:
            marker = request.args['marker'][0].strip()
            for q in range(len(entities)):
                if entities[q]['id'] == marker:
                    entities = entities[q:]
                    break
        try:
            next_marker = entities[limit]['id']
        except Exception:
            pass
        entities = entities[:limit]

        metadata = {}
        metadata['count'] = len(entities)
        metadata['limit'] = limit
        metadata['marker'] = marker
        metadata['next_marker'] = next_marker
        metadata['next_href'] = next_href
        request.setResponseCode(200)
        return json.dumps({'metadata': metadata, 'values': entities})

    @app.route('/v1.0/<string:tenant_id>/entities', methods=['POST'])
    def create_entity(self, request, tenant_id):
        """
        Creates a new entity
        """
        content = request.content.read()
        postdata = json.loads(content)
        myhostname_and_port = 'http://' + request.getRequestHostname() + ':' + self.endpoint_port
        newentity = create_entity(self._session_store.clock, postdata)
        self._entity_cache_for_tenant(tenant_id).entities_list.append(newentity)
        status = 201
        request.setResponseCode(status)
        request.setHeader('location', myhostname_and_port + request.path + '/' + newentity['id'])
        request.setHeader('x-object-id', newentity['id'])
        request.setHeader('content-type', 'text/plain')
        self._audit('entities', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>', methods=['GET'])
    def get_entity(self, request, tenant_id, entity_id):
        """
        Fetches a specific entity
        """
        entity = None
        for e in self._entity_cache_for_tenant(tenant_id).entities_list:
            if e['id'] == entity_id:
                entity = e
                break
        if not entity:
            request.setResponseCode(404)
            return '{}'
        else:
            request.setResponseCode(200)
            return json.dumps(entity)

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks', methods=['GET'])
    def get_checks_for_entity(self, request, tenant_id, entity_id):
        """
        Returns all the checks for a paricular entity
        """
        checks = []
        for c in self._entity_cache_for_tenant(tenant_id).checks_list:
            if c['entity_id'] == entity_id:
                c = dict(c)  # make a copy,  don't want the entity_id in the response
                del c['entity_id']
                checks.append(c)
        metadata = {}
        metadata['count'] = len(checks)
        metadata['limit'] = 1000
        metadata['marker'] = None
        metadata['next_marker'] = None
        metadata['next_href'] = None
        request.setResponseCode(200)
        return json.dumps({'metadata': metadata, 'values': checks})

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>', methods=['PUT'])
    def update_entity(self, request, tenant_id, entity_id):
        """
        Update entity in place.
        """
        content = request.content.read()
        update = json.loads(content)
        for q in range(len(self._entity_cache_for_tenant(tenant_id).entities_list)):
            if self._entity_cache_for_tenant(tenant_id).entities_list[q]['id'] == entity_id:
                entity = self._entity_cache_for_tenant(tenant_id).entities_list[q]
                for k in ['agent_id', 'managed', 'metadata', 'ip_addresses', 'uri', 'label']:
                    if k in update:
                        entity[k] = update[k]
                entity['updated_at'] = int(1000 * self._session_store.clock.seconds())
                break
        myhostname_and_port = 'http://' + request.getRequestHostname() + ':' + self.endpoint_port
        status = 204
        request.setResponseCode(status)
        request.setHeader('location', myhostname_and_port + request.path +
                          '/' + entity_id.encode('utf-8'))
        request.setHeader('x-object-id', entity_id.encode('utf-8'))
        request.setHeader('content-type', 'text/plain')
        self._audit('entities', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>', methods=['DELETE'])
    def delete_entity(self, request, tenant_id, entity_id):
        """
        Delete an entity, all checks that belong to entity, all alarms that belong to those checks
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities_list
        checks = self._entity_cache_for_tenant(tenant_id).checks_list
        alarms = self._entity_cache_for_tenant(tenant_id).alarms_list
        for e in range(len(entities)):
            if entities[e]['id'] == entity_id:
                del entities[e]
                break
        for c in checks:
            if c['entity_id'] == entity_id:
                del checks[checks.index(c)]
        for a in alarms:
            if a['entity_id'] == entity_id:
                del alarms[alarms.index(a)]
        status = 204
        request.setResponseCode(status)
        request.setHeader('content-type', 'text/plain')
        self._audit('entities', request, tenant_id, status)

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks', methods=['POST'])
    def create_check(self, request, tenant_id, entity_id):
        """
        Create a check
        """
        content = request.content.read()
        postdata = json.loads(content)
        myhostname_and_port = 'http://' + request.getRequestHostname() + ':' + self.endpoint_port
        newcheck = create_check(self._session_store.clock, postdata)
        newcheck['entity_id'] = entity_id
        self._entity_cache_for_tenant(tenant_id).checks_list.append(newcheck)
        status = 201
        request.setResponseCode(status)
        request.setHeader('location', myhostname_and_port + request.path + '/' + newcheck['id'])
        request.setHeader('x-object-id', newcheck['id'])
        request.setHeader('content-type', 'text/plain')
        self._audit('checks', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks/<string:check_id>',
               methods=['GET'])
    def get_check(self, request, tenant_id, entity_id, check_id):
        """
        Get a specific check that was created before
        """
        mycheck = {}
        for c in self._entity_cache_for_tenant(tenant_id).checks_list:
            if c['id'] == check_id:
                mycheck = dict(c)
                del mycheck['entity_id']
        request.setResponseCode(200)
        return json.dumps(mycheck)

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks/<string:check_id>',
               methods=['PUT'])
    def update_check(self, request, tenant_id, entity_id, check_id):
        """
        Updates a check in place.
        """
        content = request.content.read()
        update = json.loads(content)
        for check in self._entity_cache_for_tenant(tenant_id).checks_list:
            if check['entity_id'] == entity_id and check['id'] == check_id:
                for k in ['type', 'details', 'disabled', 'label', 'metadata', 'period', 'timeout',
                          'monitoring_zones_poll', 'target_alias', 'target_hostname', 'target_resolver']:
                    if k in update:
                        check[k] = update[k]
                check['updated_at'] = int(1000 * self._session_store.clock.seconds())
                break
        myhostname_and_port = 'http://' + request.getRequestHostname() + ':' + self.endpoint_port
        status = 204
        request.setResponseCode(status)
        request.setHeader('location', myhostname_and_port + request.path +
                          '/' + check_id.encode('utf-8'))
        request.setHeader('x-object-id', check_id.encode('utf-8'))
        request.setHeader('content-type', 'text/plain')
        self._audit('checks', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks/<string:check_id>',
               methods=['DELETE'])
    def delete_check(self, request, tenant_id, entity_id, check_id):
        """
        Deletes check and all alarms associated to it
        """
        checks = self._entity_cache_for_tenant(tenant_id).checks_list
        alarms = self._entity_cache_for_tenant(tenant_id).alarms_list
        for c in range(len(checks)):
            if checks[c]['entity_id'] == entity_id and checks[c]['id'] == check_id:
                del checks[c]
                break
        for a in alarms:
            if a['check_id'] == check_id and a['entity_id'] == entity_id:
                del alarms[alarms.index(a)]
        status = 204
        request.setResponseCode(status)
        request.setHeader('content-type', 'text/plain')
        self._audit('checks', request, tenant_id, status)
        return ''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms', methods=['POST'])
    def create_alarm(self, request, tenant_id, entity_id):
        """
        Creates alarm
        """
        content = request.content.read()
        postdata = json.loads(content)
        myhostname_and_port = 'http://' + request.getRequestHostname() + ':' + self.endpoint_port
        newalarm = create_alarm(self._session_store.clock, postdata)
        newalarm['entity_id'] = entity_id
        self._entity_cache_for_tenant(tenant_id).alarms_list.append(newalarm)
        status = 201
        request.setResponseCode(status)
        request.setHeader('location', myhostname_and_port + request.path + '/' + newalarm['id'])
        request.setHeader('x-object-id', newalarm['id'])
        request.setHeader('content-type', 'text/plain')
        self._audit('alarms', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms/<string:alarm_id>',
               methods=['GET'])
    def get_alarm(self, request, tenant_id, entity_id, alarm_id):
        """
        Gets an alarm by ID.
        """
        alarm = None
        for a in self._entity_cache_for_tenant(tenant_id).alarms_list:
            if a['entity_id'] == entity_id and a['id'] == alarm_id:
                alarm = a
                break
        else:
            request.setResponseCode(404)
            return json.dumps({'type': 'notFoundError',
                               'code': 404,
                               'message': 'Object does not exist',
                               'details': 'Object "Alarm" with key "{0}:{1}" does not exist'.format(
                                   entity_id, alarm_id)
                               })
        request.setResponseCode(200)
        return json.dumps(alarm)

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
        update = json.loads(content)
        for alarm in self._entity_cache_for_tenant(tenant_id).alarms_list:
            if alarm['entity_id'] == entity_id and alarm['id'] == alarm_id:
                for k in ['check_id', 'notification_plan_id', 'criteria', 'disabled', 'label',
                          'metadata']:
                    if k in update:
                        alarm[k] = update[k]
                alarm['updated_at'] = int(1000 * self._session_store.clock.seconds())
                break
        myhostname_and_port = 'http://' + request.getRequestHostname() + ':' + self.endpoint_port
        status = 204
        request.setResponseCode(status)
        request.setHeader('location', myhostname_and_port + request.path +
                          '/' + alarm_id.encode('utf-8'))
        request.setHeader('x-object-id', alarm_id.encode('utf-8'))
        request.setHeader('content-type', 'text/plain')
        self._audit('alarms', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms/<string:alarm_id>',
               methods=['DELETE'])
    def delete_alarm(self, request, tenant_id, entity_id, alarm_id):
        """
        Delete an alarm
        """
        alarms = self._entity_cache_for_tenant(tenant_id).alarms_list
        for q in range(len(alarms)):
            if alarms[q]['entity_id'] == entity_id and alarms[q]['id'] == alarm_id:
                del alarms[q]
                break
        status = 204
        request.setResponseCode(status)
        request.setHeader('content-type', 'text/plain')
        self._audit('alarms', request, tenant_id, status)
        return ''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms', methods=['GET'])
    def get_alarms_for_entity(self, request, tenant_id, entity_id):
        """
        Get all alarms for the specified entity.
        """
        alarms = [
            dict(alarm) for alarm in self._entity_cache_for_tenant(tenant_id).alarms_list
            if alarm['entity_id'] == entity_id
        ]
        for alarm in alarms:
            del alarm['entity_id']
        metadata = {}
        metadata['count'] = len(alarms)
        metadata['limit'] = 1000
        metadata['marker'] = None
        metadata['next_marker'] = None
        metadata['next_href'] = None
        request.setResponseCode(200)
        return json.dumps({'metadata': metadata, 'values': alarms})

    @app.route('/v1.0/<string:tenant_id>/views/overview', methods=['GET'])
    def overview(self, request, tenant_id):
        """
        serves the overview api call,returns all entities,checks and alarms
        """
        all_entities = self._entity_cache_for_tenant(tenant_id).entities_list
        checks = self._entity_cache_for_tenant(tenant_id).checks_list
        alarms = self._entity_cache_for_tenant(tenant_id).alarms_list
        page_limit = min(int(request.args.get('limit', [100])[0]), 1000)
        offset = 0
        current_marker = request.args.get('marker', [None])[0]
        if current_marker is not None:
            try:
                offset = all_entities.index(_MatchesID(current_marker))
            except ValueError:
                offset = 0

        entities = all_entities[offset:offset + page_limit]
        next_marker = None
        if offset + page_limit < len(all_entities):
            next_marker = all_entities[offset + page_limit]['id']

        metadata = {
            'count': len(entities),
            'marker': current_marker,
            'next_marker': next_marker,
            'limit': page_limit,
            'next_href': None
        }
        values = []
        for e in entities:
            v = {}
            v['alarms'] = []
            for a in alarms:
                if a['entity_id'] == e['id']:
                    a = dict(a)
                    del a['entity_id']
                    v['alarms'].append(a)
            v['checks'] = []
            for c in checks:
                if c['entity_id'] == e['id']:
                    c = dict(c)
                    del c['entity_id']
                    v['checks'].append(c)
            v['entity'] = e
            v['latest_alarm_states'] = []
            values.append(v)
        request.setResponseCode(200)
        return json.dumps({'metadata': metadata, 'values': values})

    @app.route('/v1.0/<string:tenant_id>/audits', methods=['GET'])
    def list_audits(self, request, tenant_id):
        """
        Gets the user's audit logs.
        """
        ordering = -1 if request.args.get('reverse', False) else 1
        all_audits = self._entity_cache_for_tenant(tenant_id).audits_list[::ordering]
        page_limit = min(int(request.args.get('limit', [100])[0]), 1000)
        offset = 0
        current_marker = request.args.get('marker', [None])[0]
        if current_marker is not None:
            try:
                offset = all_audits.index(_MatchesID(current_marker))
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
        myhostname_and_port = request.getRequestHostname() + ':' + self.endpoint_port
        mockapi_id = re.findall('/mimicking/(.+?)/', request.path)[0]
        url = "http://" + myhostname_and_port + '/mimicking/' + mockapi_id + '/ORD/v1.0'
        return json.dumps(json_home(url))

    @app.route('/v1.0/<string:tenant_id>/views/agent_host_info', methods=['GET'])
    def view_agent_host_info(self, request, tenant_id):
        """
        Return 400 until the fifth attempt, then start to return data as if the
        Agent is truly installed and working.
        """
        if 'entityId' not in request.args:
            request.setResponseCode(400)
            return json.dumps({'type': 'badRequest',
                               'code': 400,
                               'message': 'Validation error for key \'agentId, entityId, uri\'',
                               'details': 'You must specify an agentId, entityId, or an entity URI.',
                               'mimicNotes': 'But mimic will only accept entityId right now',
                               'txnId': '.fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf'})

        entity_id = request.args['entityId'][0].strip()
        for e in self._entity_cache_for_tenant(tenant_id).entities_list:
            if e['id'] == entity_id:
                agent_id = e['agent_id']
                break
        else:
            request.setResponseCode(404)
            return json.dumps({'type': 'notFoundError',
                               'code': 404,
                               'message': 'Object does not exist',
                               'details': 'Object "Entity" with key "{0}" does not exist'.format(
                                   entity_id),
                               'txnId': '.fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf'
                               })

        self._entity_cache_for_tenant(tenant_id).agenthostinfo_querycount[entity_id] += 1
        if self._entity_cache_for_tenant(tenant_id).agenthostinfo_querycount[entity_id] < 5:
            request.setResponseCode(400)
            return json.dumps({
                "type": "agentDoesNotExist",
                "code": 400,
                "message": "Agent does not exist",
                "details": "Agent XYZ does not exist.",
                "txnId": ".fake.mimic.transaction.id.c-1111111.ts-123444444.v-12344frf"
            })
        else:
            return json.dumps(agent_info(entity_id, agent_id))

    @app.route('/v1.0/<string:tenant_id>/agent_installers', methods=['POST'])
    def agent_installer(self, request, tenant_id):
        """
        URL of agent install script
        """
        xsil = "https://monitoring.api.rackspacecloud.com/"
        xsil += "v1.0/00000/agent_installers/c69b2ceafc0444506fb32255af3d9be3.sh"
        status = 201
        request.setResponseCode(status)
        request.setHeader('x-shell-installer-location', xsil)
        self._audit('agent_installers', request, tenant_id, status, request.content.read())
        return ''

    @app.route('/v1.0/<string:tenant_id>/notifications', methods=['POST'])
    def create_notification(self, request, tenant_id):
        """
        Create notification target
        """
        myhostname_and_port = 'http://' + request.getRequestHostname() + ':' + self.endpoint_port
        content = request.content.read()
        new_n = create_notification(self._session_store.clock, json.loads(content))
        self._entity_cache_for_tenant(tenant_id).notifications_list.append(new_n)
        status = 201
        request.setResponseCode(status)
        request.setHeader('content-type', 'text/plain')
        request.setHeader('location', myhostname_and_port + request.path + '/' + new_n['id'])
        request.setHeader('x-object-id', new_n['id'])
        self._audit('notifications', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/notifications', methods=['GET'])
    def get_notifications(self, request, tenant_id):
        """
        Get notification targets
        """
        nlist = self._entity_cache_for_tenant(tenant_id).notifications_list
        metadata = {'count': len(nlist), 'limit': 100, 'marker': None, 'next_marker': None,
                    'next_href': None}
        request.setResponseCode(200)
        return json.dumps({'values': nlist, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/notifications/<string:n_id>', methods=['PUT'])
    def update_notifications(self, request, tenant_id, n_id):
        """
        Updates notification targets
        """
        content = request.content.read()
        postdata = json.loads(content)
        nlist = self._entity_cache_for_tenant(tenant_id).notifications_list
        for n in nlist:
            if n['id'] == postdata['id']:
                for k in postdata.keys():
                    n[k] = postdata[k]
                n['updated_at'] = int(1000 * self._session_store.clock.seconds())
                break
        status = 204
        request.setResponseCode(status)
        request.setHeader('content-type', 'text/plain')
        self._audit('notifications', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/notifications/<string:n_id>', methods=['DELETE'])
    def delete_notification(self, request, tenant_id, n_id):
        """
        Delete a notification
        """
        nlist = self._entity_cache_for_tenant(tenant_id).notifications_list
        for n in nlist:
            if n['id'] == n_id:
                del nlist[nlist.index(n)]
                break
        status = 204
        request.setResponseCode(status)
        request.setHeader('content-type', 'text/plain')
        self._audit('notifications', request, tenant_id, status)
        return ''

    @app.route('/v1.0/<string:tenant_id>/notification_plans', methods=['POST'])
    def create_notificationplan(self, request, tenant_id):
        """
        Creates a new notificationPlans
        """
        content = request.content.read()
        postdata = json.loads(content)
        myhostname_and_port = 'http://' + request.getRequestHostname() + ':' + self.endpoint_port
        newnp = create_notification_plan(self._session_store.clock, {'label': postdata['label']})
        self._entity_cache_for_tenant(tenant_id).notificationplans_list.append(newnp)
        status = 201
        request.setResponseCode(status)
        request.setHeader('content-type', 'text/plain')
        request.setHeader('location', myhostname_and_port + request.path + '/' + newnp['id'])
        request.setHeader('x-object-id', newnp['id'])
        self._audit('notification_plans', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/notification_plans', methods=['GET'])
    def get_notification_plans(self, request, tenant_id):
        """
        Get all notification plans
        """
        npist = self._entity_cache_for_tenant(tenant_id).notificationplans_list
        metadata = {'count': len(npist), 'limit': 100, 'marker': None, 'next_marker': None,
                    'next_href': None}
        request.setResponseCode(200)
        return json.dumps({'values': npist, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/notification_plans/<string:np_id>', methods=['GET'])
    def get_notification_plan(self, request, tenant_id, np_id):
        """
        Get specific notif plan
        """
        mynp = None
        nplist = self._entity_cache_for_tenant(tenant_id).notificationplans_list
        for np in nplist:
            if np['id'] == np_id:
                mynp = np
                break
        request.setResponseCode(200)
        return json.dumps(mynp)

    @app.route('/v1.0/<string:tenant_id>/notification_plans/<string:np_id>', methods=['PUT'])
    def update_notification_plan(self, request, tenant_id, np_id):
        """
        Alter a notification plan
        """
        content = request.content.read()
        postdata = json.loads(content)
        nplist = self._entity_cache_for_tenant(tenant_id).notificationplans_list
        for np in nplist:
            if np['id'] == postdata['id']:
                for k in postdata.keys():
                    np[k] = postdata[k]
                np['updated_at'] = int(1000 * self._session_store.clock.seconds())
                break
        status = 204
        request.setResponseCode(status)
        request.setHeader('content-type', 'text/plain')
        self._audit('notification_plans', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/notification_plans/<string:np_id>', methods=['DELETE'])
    def delete_notification_plan(self, request, tenant_id, np_id):
        """
        Remove a notification plan
        """
        allalarms = self._entity_cache_for_tenant(tenant_id).alarms_list
        nplist = self._entity_cache_for_tenant(tenant_id).notificationplans_list
        alarmids_using_np = []
        for alarm in allalarms:
            if alarm['notification_plan_id'] == np_id:
                alarmids_using_np.append(alarm['id'])

        if len(alarmids_using_np):
            status = 403
            request.setResponseCode(status)
            errobj = {}
            errobj['type'] = 'forbiddenError'
            errobj['code'] = 403
            errobj['txnId'] = '.rh-D0j7.h-dfw1-maas-prod-api0.r-doc8iigF.c-5540173.ts-' + \
                str(self._session_store.clock.seconds()) + '.v-bfe87f0'
            errobj['message'] = 'Notification plans cannot be removed while alarms are using it:'
            for a_id in alarmids_using_np:
                errobj['message'] += ' ' + a_id
            errobj['details'] = errobj['message']
            self._audit('notification_plans', request, tenant_id, status)
            return json.dumps(errobj)

        for np in nplist:
            if np['id'] == np_id:
                del nplist[nplist.index(np)]
                break
        status = 204
        request.setResponseCode(status)
        request.setHeader('content-type', 'text/plain')
        self._audit('notification_plans', request, tenant_id, status)
        return ''

    @app.route('/v1.0/<string:tenant_id>/suppressions', methods=['GET'])
    def get_suppressions(self, request, tenant_id):
        """
        Get the list of suppressions for this tenant.
        """
        splist = self._entity_cache_for_tenant(tenant_id).suppressions_list
        metadata = {
            'count': len(splist),
            'limit': 100,
            'marker': None,
            'next_marker': None,
            'next_href': None
        }
        request.setResponseCode(200)
        return json.dumps({'values': splist, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/suppressions/<string:sp_id>', methods=['GET'])
    def get_suppression(self, request, tenant_id, sp_id):
        """
        Get a suppression by ID.
        """
        mysp = None
        splist = self._entity_cache_for_tenant(tenant_id).suppressions_list
        for sp in splist:
            if sp['id'] == sp_id:
                mysp = sp
                break
        request.setResponseCode(200)
        return json.dumps(mysp)

    @app.route('/v1.0/<string:tenant_id>/suppressions', methods=['POST'])
    def create_suppression(self, request, tenant_id):
        """
        Create a new suppression.
        """
        content = request.content.read()
        postdata = json.loads(content)
        myhostname_and_port = 'http://' + request.getRequestHostname() + ':' + self.endpoint_port
        newsp = create_suppression(postdata)
        self._entity_cache_for_tenant(tenant_id).suppressions_list.append(newsp)
        status = 201
        request.setResponseCode(status)
        request.setHeader('location', myhostname_and_port + request.path + '/' + newsp['id'])
        request.setHeader('x-object-id', newsp['id'])
        request.setHeader('content-type', 'text/plain')
        self._audit('suppressions', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/suppressions/<string:sp_id>', methods=['PUT'])
    def update_suppression(self, request, tenant_id, sp_id):
        """
        Update a suppression.
        """
        content = request.content.read()
        postdata = json.loads(content)
        splist = self._entity_cache_for_tenant(tenant_id).suppressions_list
        for sp in splist:
            if sp['id'] == sp_id:
                for k in postdata.keys():
                    sp[k] = postdata[k]
                sp['updated_at'] = int(1000 * self._session_store.clock.seconds())
                break
        status = 204
        request.setResponseCode(status)
        request.setHeader('content-type', 'text/plain')
        self._audit('suppressions', request, tenant_id, status, content)
        return ''

    @app.route('/v1.0/<string:tenant_id>/suppressions/<string:sp_id>', methods=['DELETE'])
    def delete_suppression(self, request, tenant_id, sp_id):
        """
        Delete a suppression.
        """
        splist = self._entity_cache_for_tenant(tenant_id).suppressions_list
        for sp in splist:
            if sp['id'] == sp_id:
                del splist[splist.index(sp)]
                break
        status = 204
        request.setResponseCode(204)
        request.setHeader('content-type', 'text/plain')
        self._audit('suppressions', request, tenant_id, status)
        return ''

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
        allalarms = self._entity_cache_for_tenant(tenant_id).alarms_list
        allnps = self._entity_cache_for_tenant(tenant_id).notificationplans_list
        values = []
        metadata = {}
        metadata['limit'] = 100
        metadata['marker'] = None
        metadata['next_marker'] = None
        metadata['next_href'] = None
        for np in allnps:
            alarm_count = 0
            v = {}
            v['notification_plan_id'] = np['id']
            for alarm in allalarms:
                if alarm['notification_plan_id'] == np['id']:
                    alarm_count = alarm_count + 1
            v['alarm_count'] = alarm_count
            values.append(v)
        metadata['count'] = len(values)
        request.setResponseCode(200)
        return json.dumps({'values': values, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/views/alarmsByNp/<string:np_id>', methods=['GET'])
    def alarms_by_np(self, request, tenant_id, np_id):
        """
        List of alarms pointing to a particular NotificationPlan
        """
        allalarms = self._entity_cache_for_tenant(tenant_id).alarms_list
        values = []
        metadata = {}
        metadata['limit'] = 100
        metadata['marker'] = None
        metadata['next_marker'] = None
        metadata['next_href'] = None
        for alarm in allalarms:
            if alarm['notification_plan_id'] == np_id:
                values.append(alarm)
        metadata['count'] = len(values)
        request.setResponseCode(200)
        return json.dumps({'values': values, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/notification_types', methods=['GET'])
    def get_notification_types(self, request, tenant_id):
        """
        Get the types of notifications supported: pageduty,email,sms, etc
        """
        ntlist = self._entity_cache_for_tenant(tenant_id).notificationtypes_list
        metadata = {'count': len(ntlist), 'limit': 100, 'marker': None, 'next_marker': None,
                    'next_href': None}
        request.setResponseCode(200)
        return json.dumps({'values': ntlist, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/views/metric_list', methods=['GET'])
    def views_metric_list(self, request, tenant_id):
        """
        All available metrics.
        """
        allchecks = self._entity_cache_for_tenant(tenant_id).checks_list
        values = []
        entities = self._entity_cache_for_tenant(tenant_id).entities_list
        for e in entities:
            values.append(create_metric_list_from_entity(e, allchecks))
        metadata = {}
        metadata['count'] = len(values)
        metadata['marker'] = None
        metadata['next_marker'] = None
        metadata['limit'] = 1000
        metadata['next_href'] = None
        request.setResponseCode(200)
        return json.dumps({'metadata': metadata, 'values': values})

    @app.route('/v1.0/<string:tenant_id>/__experiments/multiplot', methods=['POST'])
    def multiplot(self, request, tenant_id):
        """
        datapoints for all metrics requested
        Right now, only checks of type remote.ping work
        """
        allchecks = self._entity_cache_for_tenant(tenant_id).checks_list
        content = request.content.read()
        metrics_requested = json.loads(content)
        metrics_replydata = []
        for m in metrics_requested['metrics']:
            mp = create_multiplot_from_metric(m, request.args, allchecks)
            if mp:
                metrics_replydata.append(mp)
        status = 200
        request.setResponseCode(200)
        self._audit('rollups', request, tenant_id, status, content)
        return json.dumps({'metrics': metrics_replydata})
