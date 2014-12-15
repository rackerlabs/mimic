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

    def get_responsebody(self, r):
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

    def createNotification(self, label):
        """
        Util create notification
        """
        postdata = {'label': label}
        postdata['type'] = 'email'
        postdata['details'] = {'address': 'zoehardman4ever@hedkandi.co.uk'}
        req = request(self, self.root, "POST", self.uri+'/notifications', json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        return resp

    def createNotificationPlan(self, label):
        """
        Util create notification plan
        """
        postdata = {'label': label}
        req = request(self, self.root, "POST", self.uri+'/notification_plans', json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        return resp

    def createSuppression(self, label):
        postdata = {'label': label}
        req = request(self, self.root, "POST", self.uri+'/suppressions', json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        return resp

    def getXobjectIDfromResponse(self, resp):
        xobjectid = None
        for h in resp.headers.getAllRawHeaders():
            if h[0].lower() == 'x-object-id':
                xobjectid = h[1][0]
                break
        return xobjectid

    def get_ecan_objectIds(self):
        """
        Get the Entity, check, alarm an notification(plan) objects created by setUp()
        """
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)['values'][0]
        entity_id = data['entity']['id']
        check_id = data['checks'][0]['id']
        alarm_id = data['alarms'][0]['id']
        nt_id = None
        np_id = None
        sp_id = None

        req = request(self, self.root, "GET", self.uri+'/notifications', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        for nt in data['values']:
            if nt['id'] != 'ntTechnicalContactsEmail':
                nt_id = nt['id']

        req = request(self, self.root, "GET", self.uri+'/notification_plans', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        for np in data['values']:
            if np['id'] != 'npTechnicalContactsEmail':
                np_id = np['id']

        req = request(self, self.root, "GET", self.uri+'/suppressions', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        for sp in data['values']:
            sp_id = sp['id']

        return {'entity_id': entity_id, 'check_id': check_id, 'alarm_id': alarm_id,
                'nt_id': nt_id, 'np_id': np_id, 'sp_id': sp_id}

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
        nt_id = None
        np_id = None
        sp_id = None
        entity_id = self.getXobjectIDfromResponse(self.createEntity('ItsAnEntity'))
        check_id = self.getXobjectIDfromResponse(self.createCheck('ItsAcheck', entity_id))
        alarm_id = self.getXobjectIDfromResponse(self.createAlarm('ItsAnAlarm', entity_id, check_id))
        nt_id = self.getXobjectIDfromResponse(self.createNotification('ItsANotificationTarget'))
        np_id = self.getXobjectIDfromResponse(self.createNotificationPlan('ItsANotificationPlan'))
        sp_id = self.getXobjectIDfromResponse(self.createSuppression('ItsASuppression'))
        self.assertNotEquals(None, entity_id)
        self.assertNotEquals(None, check_id)
        self.assertNotEquals(None, alarm_id)
        self.assertNotEquals(None, nt_id)
        self.assertNotEquals(None, np_id)
        self.assertNotEquals(None, sp_id)

    def test_list_entity(self):
        """
        test list entity
        """
        req = request(self, self.root, "GET", self.uri+'/entities', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['metadata']['count'], 1)

    def test_get_entity(self):
        """
        test get entity
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET", self.uri+'/entities/'+ecan['entity_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(ecan['entity_id'], data['id'])

    def test_fail_get_entity(self):
        """
        test get entity
        """
        req = request(self, self.root, "GET", self.uri+'/entities/whatever', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 404)
        data = self.get_responsebody(resp)
        self.assertEquals({}, data)

    def test_get_check(self):
        """
        test get check
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET",
                      self.uri+'/entities/'+ecan['entity_id']+'/checks/'+ecan['check_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(ecan['check_id'], data['id'])

    def test_get_checks_for_entity(self):
        """
        test get check
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET",
                      self.uri+'/entities/'+ecan['entity_id']+'/checks', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(1, data['metadata']['count'])
        self.assertEquals(ecan['check_id'], data['values'][0]['id'])

    def test_update_entity(self):
        """
        update entity
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET", self.uri+'/entities/'+ecan['entity_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        data['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT", self.uri+'/entities/'+ecan['entity_id'], json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/entities/'+ecan['entity_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('Iamamwhoami', data['label'])

    def test_update_check(self):
        """
        update check
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET",
                      self.uri+'/entities/'+ecan['entity_id']+'/checks/'+ecan['check_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        data['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT",
                      self.uri+'/entities/'+ecan['entity_id']+'/checks/'+ecan['check_id'],
                      json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET",
                      self.uri+'/entities/'+ecan['entity_id']+'/checks/'+ecan['check_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('Iamamwhoami', data['label'])

    def test_update_alarm(self):
        """
        update alarm
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm = self.get_responsebody(resp)['values'][0]['alarms'][0]
        alarm['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT",
                      self.uri+'/entities/'+ecan['entity_id']+'/alarms/'+ecan['alarm_id'],
                      json.dumps(alarm))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm2 = self.get_responsebody(resp)['values'][0]['alarms'][0]
        self.assertEquals(alarm['label'], alarm2['label'])

    def test_delete_alarm(self):
        """
        delete alarm
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "DELETE",
                      self.uri+'/entities/'+ecan['entity_id']+'/alarms/'+ecan['alarm_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        self.assertEquals(0, len(self.get_responsebody(resp)['values'][0]['alarms']))

    def test_delete_check(self):
        """
        delete check
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "DELETE",
                      self.uri+'/entities/'+ecan['entity_id']+'/checks/'+ecan['check_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(0, len(data['values'][0]['checks']))
        self.assertEquals(0, len(data['values'][0]['alarms']))

    def test_delete_entity(self):
        """
        delete entity
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "DELETE",
                      self.uri+'/entities/'+ecan['entity_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(0, len(data['values']))
        self.assertEquals(0, data['metadata']['count'])

    def test_jsonhome(self):
        req = request(self, self.root, "GET", self.uri+'/__experiments/json_home', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(True, 'mimicking' in json.dumps(data))

    def test_notificationplan(self):
        """
        fetch notification plans
        """
        req = request(self, self.root, "GET", self.uri+'/notification_plans', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(True, 'npTechnicalContactsEmail' in json.dumps(data))

    def test_agenthostinfo(self):
        """
        fetch agent host info
        """
        req = request(self, self.root, "GET", self.uri+'/views/agent_host_info', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 400)
        data = self.get_responsebody(resp)
        self.assertEquals(True, 'Agent does not exist' in json.dumps(data))

    def test_metriclist(self):
        """
        get available metrics
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET", self.uri+'/views/metric_list', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(ecan['entity_id'], data['values'][0]['entity_id'])
        self.assertEquals(ecan['check_id'], data['values'][0]['checks'][0]['id'])

    def test_multiplot(self):
        """
        get datapoints for graph
        """
        ecan = self.get_ecan_objectIds()
        metrics = []
        req = request(self, self.root, "GET", self.uri+'/views/metric_list', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        for m in data['values'][0]['checks'][0]['metrics']:
            mq = {'entity_id': ecan['entity_id'], 'check_id': ecan['check_id'], 'metric': m['name']}
            metrics.append(mq)
        qstring = '?from=1412902262560&points=500&to=1412988662560'
        req = request(self, self.root, "POST",
                      self.uri+'/__experiments/multiplot'+qstring, json.dumps({'metrics': metrics}))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(500, len(data['metrics'][0]['data']))

    def test_get_all_notification_plans(self):
        """
        get all notification plans
        """
        req = request(self, self.root, "GET", self.uri+'/notification_plans', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(2, data['metadata']['count'])

    def test_get_notification_plan(self):
        """
        Get a specific notification plan
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET", self.uri+'/notification_plans/'+ecan['np_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['id'], ecan['np_id'])
        req = request(self, self.root, "GET",
                      self.uri+'/notification_plans/npTechnicalContactsEmail', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['id'], 'npTechnicalContactsEmail')

    def test_get_all_notifications(self):
        """
        Get all notification targets
        """
        req = request(self, self.root, "GET", self.uri+'/notifications', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(2, data['metadata']['count'])

    def test_update_notification(self):
        """
        Update a notification target
        """
        ecan = self.get_ecan_objectIds()
        postdata = {'id': ecan['nt_id'], 'label': 'changed'}
        req = request(self, self.root, "PUT", self.uri+'/notifications/'+ecan['nt_id'],
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/notifications', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        mynt = None
        for nt in data['values']:
            if nt['id'] == ecan['nt_id']:
                mynt = nt
                break
        self.assertNotEquals(None, mynt)
        self.assertEquals('changed', mynt['label'])

    def test_delete_notification(self):
        """
        Delete a notification target
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "DELETE", self.uri+'/notifications/'+ecan['nt_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/notifications', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        mynt = None
        for nt in data['values']:
            if nt['id'] == ecan['nt_id']:
                mynt = nt
                break
        self.assertEquals(None, mynt)

    def test_update_notificationplan(self):
        """
        Update a notification plan
        """
        ecan = self.get_ecan_objectIds()
        postdata = {'id': ecan['np_id'], 'label': 'changed'}
        req = request(self, self.root, "PUT", self.uri+'/notification_plans/'+ecan['np_id'],
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/notification_plans/'+ecan['np_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('changed', data['label'])

    def test_delete_notificationplan(self):
        """
        Delete a notification plan
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "DELETE", self.uri+'/notification_plans/'+ecan['np_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/notification_plans', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        mynp = None
        for np in data['values']:
            if np['id'] == ecan['np_id']:
                mynp = np
                break
        self.assertEquals(None, mynp)

    def test_get_notificationtypes(self):
        """
        Get notification types
        """
        req = request(self, self.root, "GET", self.uri+'/notification_types', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(4, data['metadata']['count'])

    def test_get_suppression(self):
        """
        Get a specific suppression
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET", self.uri+'/suppressions/'+ecan['sp_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['id'], ecan['sp_id'])

    def test_get_all_suppressions(self):
        """
        Get all the suppressions
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET", self.uri+'/suppressions', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(1, data['metadata']['count'])
        self.assertEquals(ecan['sp_id'], data['values'][0]['id'])

    def test_update_suppression(self):
        """
        Update an suppression
        """
        ecan = self.get_ecan_objectIds()
        postdata = {'id': ecan['sp_id'], 'label': 'changed'}
        req = request(self, self.root, "PUT", self.uri+'/suppressions/'+ecan['sp_id'],
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/suppressions/'+ecan['sp_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('changed', data['label'])

    def test_delete_suppression(self):
        """
        Delete an suppression
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "DELETE", self.uri+'/suppressions/'+ecan['sp_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/suppressions', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        mysp = None
        for sp in data['values']:
            if sp['id'] == ecan['sp_id']:
                mysp = sp
                break
        self.assertEquals(None, mysp)

    def test_alarm_count_per_np(self):
        """
        test_alarm_count_per_np
        """
        req = request(self, self.root, "GET", self.uri+'/views/alarmCountsPerNp', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['values'][0]['alarm_count'], 1)
        self.assertEquals(data['values'][0]['notification_plan_id'], 'npTechnicalContactsEmail')

    def test_alarms_by_np(self):
        """
        test_alarms_by_np
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm = self.get_responsebody(resp)['values'][0]['alarms'][0]
        alarm['notification_plan_id'] = ecan['np_id']
        req = request(self, self.root, "PUT",
                      self.uri+'/entities/'+ecan['entity_id']+'/alarms/'+ecan['alarm_id'],
                      json.dumps(alarm))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri+'/views/alarmsByNp/'+ecan['np_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['values'][0]['id'], ecan['alarm_id'])

    def test_delete_np_in_use(self):
        """
        Cant delete a notificationPlan that's being pointed to by alarms
        """
        ecan = self.get_ecan_objectIds()
        req = request(self, self.root, "GET", self.uri+'/views/overview', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm = self.get_responsebody(resp)['values'][0]['alarms'][0]
        alarm['notification_plan_id'] = ecan['np_id']
        req = request(self, self.root, "PUT",
                      self.uri+'/entities/'+ecan['entity_id']+'/alarms/'+ecan['alarm_id'],
                      json.dumps(alarm))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "DELETE", self.uri+'/notification_plans/'+ecan['np_id'], '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 403)
        data = self.get_responsebody(resp)
        self.assertTrue(ecan['alarm_id'] in data['message'])
        self.assertTrue(ecan['alarm_id'] in data['details'])

    def test_reset_session(self):
        """
        Reset session, remove all objects
        """
        req = request(self, self.root, "GET", self.uri+'/entities', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['metadata']['count'], 1)

        req = request(self, self.root, "GET", self.uri+'/mimic/reset', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)

        req = request(self, self.root, "GET", self.uri+'/entities', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['metadata']['count'], 0)
