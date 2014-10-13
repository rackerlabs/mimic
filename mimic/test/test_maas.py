import json
import treq
from twisted.trial.unittest import SynchronousTestCase
from mimic.rest.maas_api import MaasApi
from mimic.test.helpers import request
from mimic.test.fixtures import APIMockHelper


class MaasAPITests(SynchronousTestCase):
    """
    Tests for maas plugin API
    """

    def get_reposebody(self, r):
        """
        util json response body
        """
        return self.successResultOf(treq.json_content(r))

    def createEntity(self, label):
        """
        Util function entity
        """
        postdata = {}
        postdata['agent_id'] = None
        postdata['label'] = 'testCreateEntity'
        req = request(self, self.root, "POST",
                      self.uri+'/entities',
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        return resp

    def createCheck(self, label, entity_id):
        """
        Util function check
        """
        postdata = {}
        postdata['label'] = label
        postdata['details'] = {}
        postdata['monitoring_zones_poll'] = ['mzdfw', 'mzord', 'mzlon']
        postdata['target_alias'] = 'public1_v4'
        postdata['target_hostname'] = None
        postdata['target_resolver'] = None
        postdata['type'] = 'remote.ping'
        req = request(self, self.root,
                      "POST", self.uri+'/entities/'+entity_id+'/checks',
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        return resp

    def createAlarm(self, label, entity_id, check_id):
        """
        Util function alarm
        """
        postdata = {}
        postdata['check_id'] = check_id
        postdata['entityId'] = entity_id
        postdata['label'] = label
        postdata['notification_plan_id'] = 'npTechnicalContactsEmail'
        req = request(self, self.root, "POST",
                      self.uri+'/entities/'+entity_id+'/alarms',
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        return resp

    def get_eca_objectIds(self):
        """
        Get the Entity, check and alarm objects created by setUp()
        """
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)['values'][0]
        entity_id = data['entity']['id']
        check_id = data['checks'][0]['id']
        alarm_id = data['alarms'][0]['id']
        return {'entity_id': entity_id, 'check_id': check_id, 'alarm_id': alarm_id}

    def setUp(self):
        """
        Setup MaasApi helper object & uri 'n stuff
        """
        helper = APIMockHelper(self, [MaasApi(["ORD"])])
        self.root = helper.root
        self.uri = helper.uri

        entity_id = None
        check_id = None
        alarm_id = None

        resp = self.createEntity('ItsAnEntity')
        for h in resp.headers.getAllRawHeaders():
            if h[0].lower() == 'x-object-id':
                entity_id = h[1][0]
                break
        resp = self.createCheck('ItsAcheck', entity_id)
        for h in resp.headers.getAllRawHeaders():
            if h[0].lower() == 'x-object-id':
                check_id = h[1][0]
                break
        resp = self.createAlarm('ItsAnAlarm', entity_id, check_id)
        for h in resp.headers.getAllRawHeaders():
            if h[0].lower() == 'x-object-id':
                alarm_id = h[1][0]
                break

        self.assertNotEquals(None, entity_id)
        self.assertNotEquals(None, check_id)
        self.assertNotEquals(None, alarm_id)

    def test_list_entity(self):
        """
        test list entity
        """
        req = request(self, self.root, "GET", self.uri+'/entities', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals(data['metadata']['count'], 1)

    def test_get_entity(self):
        """
        test get entity
        """
        eca = self.get_eca_objectIds()
        req = request(self, self.root, "GET", self.uri+'/entities/'+eca['entity_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals(eca['entity_id'], data['id'])

    def test_fail_get_entity(self):
        """
        test get entity
        """
        req = request(self, self.root, "GET", self.uri+'/entities/whatever', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 404)
        data = self.get_reposebody(resp)
        self.assertEquals({}, data)

    def test_get_check(self):
        """
        test get check
        """
        eca = self.get_eca_objectIds()
        req = request(self, self.root, "GET",
                      self.uri+'/entities/'+eca['entity_id']+'/checks/'+eca['check_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals(eca['check_id'], data['id'])

    def test_get_checks_for_entity(self):
        """
        test get check
        """
        eca = self.get_eca_objectIds()
        req = request(self, self.root, "GET",
                      self.uri+'/entities/'+eca['entity_id']+'/checks', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals(1, data['metadata']['count'])
        self.assertEquals(eca['check_id'], data['values'][0]['id'])

    def test_update_entity(self):
        """
        update entity
        """
        eca = self.get_eca_objectIds()
        req = request(self, self.root, "GET", self.uri+'/entities/'+eca['entity_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        data['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT", self.uri+'/entities/'+eca['entity_id'], json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/entities/'+eca['entity_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals('Iamamwhoami', data['label'])

    def test_update_check(self):
        """
        update check
        """
        eca = self.get_eca_objectIds()
        req = request(self, self.root, "GET",
                      self.uri+'/entities/'+eca['entity_id']+'/checks/'+eca['check_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        data['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT",
                      self.uri+'/entities/'+eca['entity_id']+'/checks/'+eca['check_id'],
                      json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET",
                      self.uri+'/entities/'+eca['entity_id']+'/checks/'+eca['check_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals('Iamamwhoami', data['label'])

    def test_update_alarm(self):
        """
        update alarm
        """
        eca = self.get_eca_objectIds()
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm = self.get_reposebody(resp)['values'][0]['alarms'][0]
        alarm['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT",
                      self.uri+'/entities/'+eca['entity_id']+'/alarms/'+eca['alarm_id'],
                      json.dumps(alarm))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm2 = self.get_reposebody(resp)['values'][0]['alarms'][0]
        self.assertEquals(alarm['label'], alarm2['label'])

    def test_delete_alarm(self):
        """
        delete alarm
        """
        eca = self.get_eca_objectIds()
        req = request(self, self.root, "DELETE",
                      self.uri+'/entities/'+eca['entity_id']+'/alarms/'+eca['alarm_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        self.assertEquals(0, len(self.get_reposebody(resp)['values'][0]['alarms']))

    def test_delete_check(self):
        """
        delete check
        """
        eca = self.get_eca_objectIds()
        req = request(self, self.root, "DELETE",
                      self.uri+'/entities/'+eca['entity_id']+'/checks/'+eca['check_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals(0, len(data['values'][0]['checks']))
        self.assertEquals(0, len(data['values'][0]['alarms']))

    def test_delete_entity(self):
        """
        delete entity
        """
        eca = self.get_eca_objectIds()
        req = request(self, self.root, "DELETE",
                      self.uri+'/entities/'+eca['entity_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals(0, len(data['values']))
        self.assertEquals(0, data['metadata']['count'])

    def test_jsonhome(self):
        req = request(self, self.root, "GET", self.uri+'/__experiments/json_home', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals(True, 'mimicking' in json.dumps(data))

    def test_notificationplan(self):
        """
        fetch notification plans
        """
        req = request(self, self.root, "GET", self.uri+'/notification_plans', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals(True, 'npTechnicalContactsEmail' in json.dumps(data))

    def test_agenthostinfo(self):
        """
        fetch agent host info
        """
        req = request(self, self.root, "GET", self.uri+'/views/agent_host_info', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 400)
        data = self.get_reposebody(resp)
        self.assertEquals(True, 'Agent does not exist' in json.dumps(data))

    def test_metriclist(self):
        """
        get available metrics
        """
        eca = self.get_eca_objectIds()
        req = request(self, self.root, "GET", self.uri+'/views/metric_list', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals(eca['entity_id'], data['values'][0]['entity_id'])
        self.assertEquals(eca['check_id'], data['values'][0]['checks'][0]['id'])

    def test_multiplot(self):
        """
        get datapoints for graph
        """
        eca = self.get_eca_objectIds()
        metrics = []
        req = request(self, self.root, "GET", self.uri+'/views/metric_list', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        for m in data['values'][0]['checks'][0]['metrics']:
            mq = {'entity_id': eca['entity_id'], 'check_id': eca['check_id'], 'metric': m['name']}
            metrics.append(mq)
        qstring = '?from=1412902262560&points=500&to=1412988662560'
        req = request(self, self.root, "POST",
                      self.uri+'/__experiments/multiplot'+qstring, json.dumps({'metrics': metrics}))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_reposebody(resp)
        self.assertEquals(500, len(data['metrics'][0]['data']))
