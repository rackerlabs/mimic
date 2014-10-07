"""
MAAS Mock API
"""

import json
import collections
import time
import random
import string
import re
from uuid import uuid4

from six import text_type

from zope.interface import implementer

from twisted.web.server import Request
from twisted.plugin import IPlugin

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.rest.mimicapp import MimicApp
from mimic.imimic import IAPIMock


Request.defaultContentType = 'application/json'


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


class M_Cache(dict):
    """
    M(onitoring) Cache Object to hold dictionaries of all entities, checks and alarms.
    """
    def __init__(self):
        """
        Create the initial structs for cache
        """
        self.json_home = json.loads(file('mimic/rest/cloudMonitoring_json_home.json').read())
        self.entities_list = []
        self.checks_list = []
        self.alarms_list = []


def createEntity(params):
    """
    Returns a dictionary representing an entity
    """
    params = collections.defaultdict(lambda: '', params)
    newentity = {}
    newentity['label'] = params[u'label'].encode("ascii")
    newentity['id'] = newentity['label'] + ''.join(random.sample(string.letters + string.digits, 8))
    newentity['agent_id'] = params['agent_id'] or ''.join(
        random.sample(string.letters + string.digits, 24))
    newentity['created_at'] = time.time()
    newentity['updated_at'] = time.time()
    newentity['managed'] = params['managed']
    newentity['metadata'] = params['metadata']
    newentity['ip_addresses'] = (params['ip_addresses'] or
                                 {'access_ip0_v6': '2001: 4800: 7812: 0514: 6eaf: ff05: 93d7',
                                  'access_ip1_v4': '133.713.371.337',
                                  'private0_v4': '10.177.177.12',
                                  'public0_v6': '2001: 4800: 7812: 0514: 6eaf: ff05: 93d7',
                                  'public1_v4': '166.78.78.19'})
    return newentity


def createCheck(params):
    """
    Returns a dictionary representing a check
    """
    params = collections.defaultdict(lambda: '', params)
    for k in params.keys():
        if 'encode' in dir(params[k]):
            params[k] = params[k].encode('ascii')
    params['id'] = params['label'] + ''.join(random.sample(string.letters + string.digits, 8))
    params['collectors'] = []
    for q in range(3):
        params['collectors'].append('co'.join(random.sample(string.letters + string.digits, 6)))
    params['confd_hash'] = None
    params['confd_name'] = None
    params['created_at'] = time.time()
    params['updated_at'] = time.time()
    params['timeout'] = 10
    params['period'] = 60
    params['disabled'] = False
    params['metadata'] = None
    params['target_alias'] = None
    if 'count' not in params['details']:
        params['details'] = {'count': 5}  # I have no idea what count=5 is for.
    return params


def createAlarm(params):
    """
    Returns a dictionary representing an alarm
    """
    params = collections.defaultdict(lambda: '', params)
    for k in params.keys():
        if 'encode' in dir(params[k]):
            params[k] = params[k].encode('ascii')
    params['id'] = params['label'] + ''.join(random.sample(string.letters + string.digits, 6))
    params['confd_hash'] = None
    params['confd_name'] = None
    params['created_at'] = time.time()
    params['updated_at'] = time.time()
    params['disabled'] = False
    params['metadata'] = None
    return params


def createMetriclistFromEntity(entity, allchecks):
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
                    {'name': mz.encode('ascii') + '.available', 'unit': 'percent', 'type': 'D'})
                metricscheck['metrics'].append(
                    {'name': mz.encode('ascii') + '.average', 'unit': 'seconds', 'type': 'D'})
            v['checks'].append(metricscheck)
    return v


def createMultiplotFromMetric(metric, reqargs, allchecks):
    """
    Given a metric, this will produce fake datapoints to graph
    This is for the multiplot API call
    """
    fromdate = int(reqargs['from'][0])
    todate = int(reqargs['to'][0])
    points = int(reqargs['points'][0])
    multiplot = {}
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
                for q in range(points + 1):
                    d = {}
                    d['numPoints'] = 4
                    d['timestamp'] = timestamp
                    d['average'] = random.randint(1, 99)
                    multiplot['data'].append(d)
                    timestamp += interval

    return multiplot


class MaasMock(object):
    """
    Klein routes for the Monitoring API.
    """
    def __init__(self, api_mock, uri_prefix, session_store, name):
        """
        Create a maas region with a given URI prefix (used for generating URIs
        to servers).
        """
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._name = name

    def _entity_cache_for_tenant(self, tenant_id):
        """
        Retrieve the M_cache object containing all objects created so far
        """
        return (self._session_store.session_for_tenant_id(tenant_id)
                .data_for_api(self._api_mock, lambda: collections.defaultdict(M_Cache))[self._name]
                )

    app = MimicApp()

    @app.route('/v1.0/<string:tenant_id>/entities', methods=['GET'])
    def list_entities(self, request, tenant_id):
        """
        Replies the entities list call
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities_list
        metadata = {}
        metadata['count'] = len(entities)
        metadata['limit'] = 1000
        metadata['marker'] = None
        metadata['next_marker'] = None
        metadata['next_href'] = None
        request.setResponseCode(200)
        return json.dumps({'metadata': metadata, 'values': entities})

    @app.route('/v1.0/<string:tenant_id>/entities', methods=['POST'])
    def create_entity(self, request, tenant_id):
        """
        Creates a new entity
        """
        postdata = json.loads(request.content.read())
        myhostname_and_port = 'http: //' + request.getRequestHostname() + ": 8900"
        newentity = createEntity({'label': postdata[u'label'].encode('ascii')})
        self._entity_cache_for_tenant(tenant_id).entities_list.append(newentity)
        request.setResponseCode(201)
        request.setHeader('location', myhostname_and_port + request.path + '/' + newentity['id'])
        request.setHeader('x-object-id', newentity['id'])
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
        Update entity. I really just delete it and then put a new one, but with the same id
        so I don't mess up relationships to checks & alarms
        """
        newentity = createEntity(json.loads(request.content.read()))
        newentity['id'] = entity_id
        for k in newentity.keys():
            if 'encode' in dir(newentity[k]):  # because there are integers sometimes.
                newentity[k] = newentity[k].encode('ascii')
        for q in range(len(self._entity_cache_for_tenant(tenant_id).entities_list)):
            if self._entity_cache_for_tenant(tenant_id).entities_list[q]['id'] == entity_id:
                del self._entity_cache_for_tenant(tenant_id).entities_list[q]
                self._entity_cache_for_tenant(tenant_id).entities_list.append(newentity)
                break
        myhostname_and_port = 'http: //' + request.getRequestHostname() + ": 8900"
        request.setResponseCode(204)
        request.setHeader('location', myhostname_and_port + request.path + '/' + newentity['id'])
        request.setHeader('x-object-id', newentity['id'])
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
        for c in range(len(checks)):
            if checks[c]['entity_id'] == entity_id:
                del checks[c]
        for a in range(len(alarms)):
            if alarms[a]['entity_id'] == entity_id:
                del alarms[a]
        request.setResponseCode(204)

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks', methods=['POST'])
    def create_check(self, request, tenant_id, entity_id):
        """
        Create a check
        """
        postdata = json.loads(request.content.read())
        myhostname_and_port = 'http: //' + request.getRequestHostname() + ": 8900"
        newcheck = createCheck(postdata)
        newcheck['entity_id'] = entity_id
        self._entity_cache_for_tenant(tenant_id).checks_list.append(newcheck)
        request.setResponseCode(201)
        request.setHeader('location', myhostname_and_port + request.path + '/' + newcheck['id'])
        request.setHeader('x-object-id', newcheck['id'])
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
        Update an existing check
        """
        checks = self._entity_cache_for_tenant(tenant_id).checks_list
        newcheck = json.loads(request.content.read())
        newcheck['entity_id'] = entity_id
        for k in newcheck.keys():
            if 'encode' in dir(newcheck[k]):  # because there are integers sometimes.
                newcheck[k] = newcheck[k].encode('ascii')
        for q in range(len(checks)):
            if checks[q]['entity_id'] == entity_id and checks[q]['id'] == check_id:
                del checks[q]
                checks.append(newcheck)
                break
        myhostname_and_port = 'http: //' + request.getRequestHostname() + ": 8900"
        request.setResponseCode(204)
        request.setHeader('location', myhostname_and_port + request.path + '/' + newcheck['id'])
        request.setHeader('x-object-id', newcheck['id'])
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
        for a in range(len(alarms)):
            if alarms[a]['check_id'] == check_id and alarms[a]['entity_id'] == entity_id:
                del alarms[a]
        request.setResponseCode(204)

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms', methods=['POST'])
    def create_alarm(self, request, tenant_id, entity_id):
        """
        Creates alarm
        """
        postdata = json.loads(request.content.read())
        myhostname_and_port = 'http: //' + request.getRequestHostname() + ": 8900"
        newalarm = createAlarm(postdata)
        newalarm['entity_id'] = entity_id
        self._entity_cache_for_tenant(tenant_id).alarms_list.append(newalarm)
        request.setResponseCode(201)
        request.setHeader('location', myhostname_and_port + request.path + '/' + newalarm['id'])
        request.setHeader('x-object-id', newalarm['id'])
        return ''

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/alarms/<string:alarm_id>',
               methods=['PUT'])
    def update_alarm(self, request, tenant_id, entity_id, alarm_id):
        """
        update alarm
        """
        alarms = self._entity_cache_for_tenant(tenant_id).alarms_list
        newalarm = json.loads(request.content.read())
        newalarm['entity_id'] = entity_id
        newalarm['updated_at'] = time.time()
        newalarm['check_id'] = re.findall('.*checks/(.*)', request.getHeader('Referer'))[0]
        for k in newalarm.keys():
            if 'encode' in dir(newalarm[k]):  # because there are integers sometimes.
                newalarm[k] = newalarm[k].encode('ascii')
        for q in range(len(alarms)):
            if alarms[q]['entity_id'] == entity_id and alarms[q]['id'] == alarm_id:
                del alarms[q]
                alarms.append(newalarm)
                break
        myhostname_and_port = 'http: //' + request.getRequestHostname() + ": 8900"
        request.setResponseCode(204)
        request.setHeader('location', myhostname_and_port + request.path + '/' + newalarm['id'])
        request.setHeader('x-object-id', newalarm['id'])
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
        request.setResponseCode(204)

    @app.route('/v1.0/<string:tenant_id>/views/overview', methods=['GET'])
    def overview(self, request, tenant_id):
        """
        serves the overview api call,returns all entities,checks and alarms
        """
        entities = self._entity_cache_for_tenant(tenant_id).entities_list
        checks = self._entity_cache_for_tenant(tenant_id).checks_list
        alarms = self._entity_cache_for_tenant(tenant_id).alarms_list
        metadata = {}
        metadata['count'] = len(entities)
        metadata['marker'] = None
        metadata['next_marker'] = None
        metadata['limit'] = 1000
        metadata['next_href'] = None
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

    @app.route('/v1.0/<string:tenant_id>/__experiments/json_home', methods=['GET'])
    def service_json_home(self, request, tenant_id):
        """
        jsonhome call. CloudIntellgiences doesn't actually use these URLs directly.
        Rather, do some regex on them to figure how to know what permissions the user as
        have
        """
        cache = self._entity_cache_for_tenant(tenant_id)
        request.setResponseCode(200)
        myhostname_and_port = request.getRequestHostname() + ":8900"
        mockapi_id = re.findall('/mimicking/(.+?)/', request.path)[0]
        return json.dumps(cache.json_home)\
            .replace('.com/v1.0', '.com/mimicking/' + mockapi_id + '/ORD/v1.0')\
            .replace('monitoring.api.rackspacecloud.com', myhostname_and_port)\
            .replace("https://", "http://")

    @app.route('/v1.0/<string:tenant_id>/views/agent_host_info', methods=['GET'])
    def view_agent_host_info(self, request, tenant_id):
        """
        No agent minitoring. For now, alwyas return 400.
        """
        request.setResponseCode(400)
        return """{
          "type":  "agentDoesNotExist",
          "code":  400,
          "message":  "Agent does not exist",
          "details":  "Agent c302622d-7612-4485-af8b-8363d8ce9184 does not exist.",
          "txnId":  ".rh-quqy.h-ord1-maas-prod-api1.r-1wej75Ht.c-21273930.ts-1410911874749.v-858fee7"
        }"""

    @app.route('/v1.0/<string:tenant_id>/notification_plans', methods=['GET'])
    def get_notification_plans(self, request, tenant_id):
        """
        In the future, user can create own on and use it however the please.
        For now, hardcored response. But will have to change this to an array of some kind.
        """
        values = [{'id': 'npTechnicalContactsEmail', 'label': 'Technical Contacts - Email',
                  'critical_state': [], 'warning_state': [], 'ok_state': [], 'metadata': None}]
        metadata = {'count': 1, 'limit': 100, 'marker': None, 'next_marker': None, 'next_href': None}
        request.setResponseCode(200)
        return json.dumps({'values': values, 'metadata': metadata})

    @app.route('/v1.0/<string:tenant_id>/views/metric_list', methods=['GET'])
    def views_metric_list(self, request, tenant_id):
        """
        All available metrics.
        """
        allchecks = self._entity_cache_for_tenant(tenant_id).checks_list
        values = []
        entities = self._entity_cache_for_tenant(tenant_id).entities_list
        for e in entities:
            values.append(createMetriclistFromEntity(e, allchecks))
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
        metrics_requested = json.loads(request.content.read())
        metrics_replydata = []
        for m in metrics_requested['metrics']:
            mp = createMultiplotFromMetric(m, request.args, allchecks)
            if mp:
                metrics_replydata.append(mp)
        request.setResponseCode(200)
        return json.dumps({'metrics': metrics_replydata})
