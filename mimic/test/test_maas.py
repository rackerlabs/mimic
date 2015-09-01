import json
import treq
from twisted.trial.unittest import SynchronousTestCase
from mimic.rest.maas_api import MaasApi, MaasControlApi
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
        postdata['label'] = label
        req = request(self, self.root, "POST",
                      self.uri + '/entities',
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
                      "POST", self.uri + '/entities/' + entity_id + '/checks',
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
                      self.uri + '/entities/' + entity_id + '/alarms',
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
        req = request(self, self.root, "POST", self.uri + '/notifications', json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        return resp

    def createNotificationPlan(self, label):
        """
        Util create notification plan
        """
        postdata = {'label': label}
        req = request(self, self.root, "POST", self.uri + '/notification_plans', json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        return resp

    def createSuppression(self, label):
        postdata = {'label': label}
        req = request(self, self.root, "POST", self.uri + '/suppressions', json.dumps(postdata))
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

    def setUp(self):
        """
        Setup MaasApi helper object & uri 'n stuff
        """
        maas = MaasApi(["ORD"])
        helper = APIMockHelper(self, [maas, MaasControlApi(maas_api=maas)])
        self.root = helper.root
        self.uri = helper.uri
        self.ctl_uri = helper.auth.get_service_endpoint("cloudMonitoringControl", "ORD")
        self.entity_id = self.getXobjectIDfromResponse(self.createEntity('ItsAnEntity'))
        self.check_id = self.getXobjectIDfromResponse(self.createCheck('ItsAcheck',
                                                                       self.entity_id))
        self.alarm_id = self.getXobjectIDfromResponse(self.createAlarm('ItsAnAlarm',
                                                                       self.entity_id,
                                                                       self.check_id))
        self.nt_id = self.getXobjectIDfromResponse(self.createNotification('ItsANotificationTarget'))
        self.np_id = self.getXobjectIDfromResponse(self.createNotificationPlan('ItsANotificationPlan'))
        self.sp_id = self.getXobjectIDfromResponse(self.createSuppression('ItsASuppression'))

    def test_resource_ids(self):
        """
        MAAS sets IDs for resources it created by prefixing it with the
        first two characters of the resource type.For example an entity
        id is prefixed with 'en'. Test that the ids are not null and are
        prefixed.
        """
        self.assertNotEquals(None, self.entity_id)
        self.assertTrue(self.entity_id.startswith('en'))
        self.assertNotEquals(None, self.check_id)
        self.assertTrue(self.check_id.startswith('ch'))
        self.assertNotEquals(None, self.alarm_id)
        self.assertTrue(self.alarm_id.startswith('al'))
        self.assertNotEquals(None, self.nt_id)
        self.assertTrue(self.nt_id.startswith('nt'))
        self.assertNotEquals(None, self.np_id)
        self.assertTrue(self.np_id.startswith('np'))
        self.assertNotEquals(None, self.sp_id)
        self.assertTrue(self.sp_id.startswith('sp'))

    def test_list_entity(self):
        """
        test list entity
        """
        req = request(self, self.root, "GET", self.uri + '/entities')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['metadata']['count'], 1)
        for q in range(1, 101):
            self.createEntity('Cinnamon' + str(q))
        for q in range(1, 101):
            req = request(self, self.root, "GET", self.uri + '/entities/?limit=' + str(q))
            resp = self.successResultOf(req)
            self.assertEquals(resp.code, 200)
            data = self.get_responsebody(resp)
            self.assertEquals(data['metadata']['count'], q)
            marker = data['metadata']['next_marker']
        req = request(self, self.root, "GET", self.uri + '/entities/?marker=' + marker)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['metadata']['count'], 1)
        self.assertEquals(data['metadata']['next_marker'], None)

    def test_get_entity(self):
        """
        test get entity
        """
        req = request(self, self.root, "GET", self.uri + '/entities/' + self.entity_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(self.entity_id, data['id'])

    def test_fail_get_entity(self):
        """
        test get entity
        """
        req = request(self, self.root, "GET", self.uri + '/entities/whatever')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 404)
        data = self.get_responsebody(resp)
        self.assertEquals({}, data)

    def test_list_audits(self):
        """
        Test getting the audit log.
        """
        req = request(self, self.root, "GET", self.uri + '/audits?limit=2')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['metadata']['count'], 2)
        self.assertEquals(data['values'][0]['app'], 'entities')

        req = request(self, self.root, "GET", self.uri +
                      '/audits?marker=' + data['metadata']['next_marker'])
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['metadata']['count'], 4)
        self.assertEquals(data['values'][0]['app'], 'alarms')

    def test_list_audits_reverse(self):
        """
        Test getting the audit log with `reverse` set to True.
        """
        req = request(self, self.root, "GET", self.uri + '/audits?limit=2&reverse=true')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['metadata']['count'], 2)
        self.assertEquals(data['values'][0]['app'], 'suppressions')

    def test_list_audits_marker_not_found(self):
        """
        If the marker is not found, the audit log returns results from the
        beginning.
        """
        req = request(self, self.root, "GET", self.uri +
                      '/audits?marker=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['values'][0]['app'], 'entities')

    def test_get_check(self):
        """
        test get check
        """
        req = request(self, self.root, "GET",
                      self.uri + '/entities/' + self.entity_id + '/checks/' + self.check_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(self.check_id, data['id'])

    def test_get_checks_for_entity(self):
        """
        test get check
        """
        req = request(self, self.root, "GET",
                      self.uri + '/entities/' + self.entity_id + '/checks')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(1, data['metadata']['count'])
        self.assertEquals(self.check_id, data['values'][0]['id'])

    def test_update_entity(self):
        """
        update entity
        """
        req = request(self, self.root, "GET", self.uri + '/entities/' + self.entity_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        data['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT", self.uri + '/entities/' +
                      self.entity_id, json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/entities/' + self.entity_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('Iamamwhoami', data['label'])

    def test_partial_update_entity(self):
        """
        Update an entity, fields not specified in the body don't change.
        """
        data = {'agent_id': 'ag13378901234'}
        req = request(self, self.root, "PUT", self.uri + '/entities/' + self.entity_id, json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/entities/' + self.entity_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('ag13378901234', data['agent_id'])
        self.assertEquals('ItsAnEntity', data['label'])

    def test_get_alarm(self):
        """
        The URL /entities/<entity_id>/alarms/<alarm_id> returns a JSON
        description of the alarm.

        """
        req = request(self, self.root, "GET",
                      self.uri + '/entities/' + self.entity_id + '/alarms/' + self.alarm_id, '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(self.alarm_id, data['id'])

    def test_get_nonexistent_alarm(self):
        """
        Getting an alarm that does not exist should 404
        """
        req = request(self, self.root, "GET",
                      self.uri + '/entities/' + self.entity_id + '/alarms/alDoesNotExist', '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 404)

    def test_update_check(self):
        """
        update check
        """
        req = request(self, self.root, "GET",
                      self.uri + '/entities/' + self.entity_id + '/checks/' + self.check_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        data['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT",
                      self.uri + '/entities/' + self.entity_id + '/checks/' + self.check_id,
                      json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET",
                      self.uri + '/entities/' + self.entity_id + '/checks/' + self.check_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('Iamamwhoami', data['label'])

    def test_partial_update_check(self):
        """
        Update a check, fields not specified in the body don't change.
        """
        data = {'target_alias': 'internet7_v4'}
        req = request(self, self.root, "PUT",
                      self.uri + '/entities/' + self.entity_id + '/checks/' + self.check_id,
                      json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET",
                      self.uri + '/entities/' + self.entity_id + '/checks/' + self.check_id, '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('internet7_v4', data['target_alias'])
        self.assertEquals('ItsAcheck', data['label'])

    def test_update_alarm(self):
        """
        update alarm
        """
        req = request(self, self.root, "GET", self.uri + '/views/overview')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm = self.get_responsebody(resp)['values'][0]['alarms'][0]
        alarm['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT",
                      self.uri + '/entities/' + self.entity_id + '/alarms/' + self.alarm_id,
                      json.dumps(alarm))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/views/overview')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm2 = self.get_responsebody(resp)['values'][0]['alarms'][0]
        self.assertEquals(alarm['label'], alarm2['label'])

    def test_partial_update_alarm(self):
        """
        When a request is received that updates an alarm, fields not specified
        in that request's body remain the same.

        """
        data = {'notification_plan_id': 'np123456'}
        req = request(self, self.root, "PUT",
                      self.uri + '/entities/' + self.entity_id + '/alarms/' + self.alarm_id,
                      json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET",
                      self.uri + '/entities/' + self.entity_id + '/alarms/' + self.alarm_id, '')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('np123456', data['notification_plan_id'])
        self.assertEquals('ItsAnAlarm', data['label'])

    def test_delete_alarm(self):
        """
        delete alarm
        """
        req = request(self, self.root, "DELETE",
                      self.uri + '/entities/' + self.entity_id + '/alarms/' + self.alarm_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/views/overview')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        self.assertEquals(0, len(self.get_responsebody(resp)['values'][0]['alarms']))

    def test_test_alarm_400s_when_empty_queue(self):
        """
        The test-alarm API should return a 400 when no simulated responses
        have been created yet.
        """
        req = request(self, self.root, "POST",
                      self.uri + '/entities/' + self.entity_id + '/test-alarm',
                      json.dumps({'criteria': 'return new AlarmStatus(OK);',
                                  'check_data': [{}]}))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 400)
        data = self.get_responsebody(resp)
        self.assertEquals('No configured test-alarm responses', data['message'])

    def test_test_alarm(self):
        """
        Test test-alarm API in normal operation.
        """
        req = request(self, self.root, "POST",
                      self.ctl_uri + '/entities/' + self.entity_id + '/alarms/test_responses',
                      json.dumps({'state': 'OK',
                                  'status': 'test-alarm working OK'}))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        req = request(self, self.root, "POST",
                      self.uri + '/entities/' + self.entity_id + '/test-alarm',
                      json.dumps({'criteria': 'return new AlarmStatus(OK);',
                                  'check_data': [{}]}))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(1, len(data))
        self.assertEquals('OK', data[0]['state'])
        self.assertEquals('test-alarm working OK', data[0]['status'])
        self.assertIn('timestamp', data[0])

    def test_get_alarms_for_entity(self):
        """
        get all alarms for the entity
        """
        req = request(self, self.root, "GET",
                      self.uri + '/entities/' + self.entity_id + '/alarms')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(1, data['metadata']['count'])
        self.assertEquals(self.alarm_id, data['values'][0]['id'])

    def test_delete_check(self):
        """
        delete check
        """
        req = request(self, self.root, "DELETE",
                      self.uri + '/entities/' + self.entity_id + '/checks/' + self.check_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/views/overview')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(0, len(data['values'][0]['checks']))
        self.assertEquals(0, len(data['values'][0]['alarms']))

    def test_delete_entity(self):
        """
        delete entity
        """
        req = request(self, self.root, "DELETE",
                      self.uri + '/entities/' + self.entity_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/views/overview')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(0, len(data['values']))
        self.assertEquals(0, data['metadata']['count'])

    def test_jsonhome(self):
        req = request(self, self.root, "GET", self.uri + '/__experiments/json_home')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(True, 'mimicking' in json.dumps(data))

    def test_notificationplan(self):
        """
        fetch notification plans
        """
        req = request(self, self.root, "GET", self.uri + '/notification_plans')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(True, 'npTechnicalContactsEmail' in json.dumps(data))

    def test_agenthostinfo(self):
        """
        fetch agent host info
        """
        for q in range(4):
            req = request(self, self.root, "GET",
                          self.uri + '/views/agent_host_info?entityId=' + self.entity_id)
            resp = self.successResultOf(req)
            self.assertEquals(resp.code, 400)
            data = self.get_responsebody(resp)
            self.assertEquals(True, 'Agent does not exist' in json.dumps(data))
        req = request(self, self.root, "GET",
                      self.uri + '/views/agent_host_info?entityId=' + self.entity_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(True, self.entity_id == data['values'][0]['entity_id'])
        req = request(self, self.root, "GET",
                      self.uri + '/views/agent_host_info')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 400)
        data = self.get_responsebody(resp)
        self.assertEquals(True, data['type'] == 'badRequest')
        req = request(self, self.root, "GET",
                      self.uri + '/views/agent_host_info?entityId=enDoesNotExist')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 404)
        data = self.get_responsebody(resp)
        self.assertEquals(data['type'], 'notFoundError')

    def test_agentinstallers(self):
        """
        fetch agent installer
        """
        req = request(self, self.root, "POST", self.uri + '/agent_installers')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        xsil = resp.headers.getRawHeaders('x-shell-installer-location')
        self.assertTrue(xsil is not None)
        self.assertTrue('monitoring.api' in xsil[0])

    def test_metriclist(self):
        """
        get available metrics
        """
        req = request(self, self.root, "GET", self.uri + '/views/metric_list')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(self.entity_id, data['values'][0]['entity_id'])
        self.assertEquals(self.check_id, data['values'][0]['checks'][0]['id'])

    def test_multiplot(self):
        """
        get datapoints for graph
        """
        metrics = []
        req = request(self, self.root, "GET", self.uri + '/views/metric_list')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        for m in data['values'][0]['checks'][0]['metrics']:
            mq = {'entity_id': self.entity_id, 'check_id': self.check_id, 'metric': m['name']}
            metrics.append(mq)
        qstring = '?from=1412902262560&points=500&to=1412988662560'
        req = request(self, self.root, "POST",
                      self.uri + '/__experiments/multiplot' + qstring, json.dumps({'metrics': metrics}))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(500, len(data['metrics'][0]['data']))

    def test_multiplot_squarewave(self):
        """
        get datapoints for graph, specifically squarewave PING check graph
        """
        metrics = []
        squarewave_check_id = self.getXobjectIDfromResponse(self.createCheck('squarewave',
                                                                             self.entity_id))
        req = request(self, self.root, "GET", self.uri + '/views/metric_list')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        for m in data['values'][0]['checks'][0]['metrics']:
            mq = {'entity_id': self.entity_id, 'check_id': squarewave_check_id, 'metric': m['name']}
            metrics.append(mq)
        qstring = '?from=1412902262560&points=500&to=1412988662560'
        req = request(self, self.root, "POST",
                      self.uri + '/__experiments/multiplot' + qstring, json.dumps({'metrics': metrics}))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(500, len(data['metrics'][0]['data']))

    def test_get_all_notification_plans(self):
        """
        get all notification plans
        """
        req = request(self, self.root, "GET", self.uri + '/notification_plans')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(2, data['metadata']['count'])

    def test_get_notification_plan(self):
        """
        Get a specific notification plan
        """
        req = request(self, self.root, "GET", self.uri + '/notification_plans/' + self.np_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['id'], self.np_id)
        req = request(self, self.root, "GET",
                      self.uri + '/notification_plans/npTechnicalContactsEmail')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['id'], 'npTechnicalContactsEmail')

    def test_get_all_notifications(self):
        """
        Get all notification targets
        """
        req = request(self, self.root, "GET", self.uri + '/notifications')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(2, data['metadata']['count'])

    def test_update_notification(self):
        """
        Update a notification target
        """
        postdata = {'id': self.nt_id, 'label': 'changed'}
        req = request(self, self.root, "PUT", self.uri + '/notifications/' + self.nt_id,
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/notifications')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        mynt = None
        for nt in data['values']:
            if nt['id'] == self.nt_id:
                mynt = nt
                break
        self.assertNotEquals(None, mynt)
        self.assertEquals('changed', mynt['label'])

    def test_delete_notification(self):
        """
        Delete a notification target
        """
        req = request(self, self.root, "DELETE", self.uri + '/notifications/' + self.nt_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/notifications')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        mynt = None
        for nt in data['values']:
            if nt['id'] == self.nt_id:
                mynt = nt
                break
        self.assertEquals(None, mynt)

    def test_update_notificationplan(self):
        """
        Update a notification plan
        """
        postdata = {'id': self.np_id, 'label': 'changed'}
        req = request(self, self.root, "PUT", self.uri + '/notification_plans/' + self.np_id,
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/notification_plans/' + self.np_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('changed', data['label'])

    def test_delete_notificationplan(self):
        """
        Delete a notification plan
        """
        req = request(self, self.root, "DELETE", self.uri + '/notification_plans/' + self.np_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/notification_plans')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        mynp = None
        for np in data['values']:
            if np['id'] == self.np_id:
                mynp = np
                break
        self.assertEquals(None, mynp)

    def test_get_notificationtypes(self):
        """
        Get notification types
        """
        req = request(self, self.root, "GET", self.uri + '/notification_types')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(4, data['metadata']['count'])

    def test_get_suppression(self):
        """
        Get a specific suppression
        """
        req = request(self, self.root, "GET", self.uri + '/suppressions/' + self.sp_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['id'], self.sp_id)
        self.assertEquals(data['notification_plans'], [])
        self.assertEquals(data['entities'], [])
        self.assertEquals(data['checks'], [])
        self.assertEquals(data['alarms'], [])

    def test_get_all_suppressions(self):
        """
        Get all the suppressions
        """
        req = request(self, self.root, "GET", self.uri + '/suppressions')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(1, data['metadata']['count'])
        self.assertEquals(self.sp_id, data['values'][0]['id'])

    def test_update_suppression(self):
        """
        Update an suppression
        """
        postdata = {'id': self.sp_id, 'label': 'changed'}
        req = request(self, self.root, "PUT", self.uri + '/suppressions/' + self.sp_id,
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/suppressions/' + self.sp_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals('changed', data['label'])

    def test_delete_suppression(self):
        """
        Delete an suppression
        """
        req = request(self, self.root, "DELETE", self.uri + '/suppressions/' + self.sp_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/suppressions')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        mysp = None
        for sp in data['values']:
            if sp['id'] == self.sp_id:
                mysp = sp
                break
        self.assertEquals(None, mysp)

    def test_list_monitoring_zones(self):
        """
        List the monitoring zones
        """
        req = request(self, self.root, "GET", self.uri + '/monitoring_zones')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        mz = data['values'][0]
        self.assertEquals('mzdfw', mz['id'])

    def test_list_alarm_examples(self):
        """
        List the alarm examples
        """
        req = request(self, self.root, "GET", self.uri + '/alarm_examples')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        ax = data['values'][0]
        self.assertEquals('remote.http_body_match_1', ax['id'])

    def test_alarm_count_per_np(self):
        """
        test_alarm_count_per_np
        """
        req = request(self, self.root, "GET", self.uri + '/views/alarmCountsPerNp')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['values'][0]['alarm_count'], 1)
        self.assertEquals(data['values'][0]['notification_plan_id'], 'npTechnicalContactsEmail')

    def test_alarms_by_np(self):
        """
        test_alarms_by_np
        """
        req = request(self, self.root, "GET", self.uri + '/views/overview')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm = self.get_responsebody(resp)['values'][0]['alarms'][0]
        alarm['notification_plan_id'] = self.np_id
        req = request(self, self.root, "PUT",
                      self.uri + '/entities/' + self.entity_id + '/alarms/' + self.alarm_id,
                      json.dumps(alarm))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "GET", self.uri + '/views/alarmsByNp/' + self.np_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['values'][0]['id'], self.alarm_id)

    def test_delete_np_in_use(self):
        """
        Cant delete a notificationPlan that's being pointed to by alarms
        """
        req = request(self, self.root, "GET", self.uri + '/views/overview')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm = self.get_responsebody(resp)['values'][0]['alarms'][0]
        alarm['notification_plan_id'] = self.np_id
        req = request(self, self.root, "PUT",
                      self.uri + '/entities/' + self.entity_id + '/alarms/' + self.alarm_id,
                      json.dumps(alarm))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        req = request(self, self.root, "DELETE", self.uri + '/notification_plans/' + self.np_id)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 403)
        data = self.get_responsebody(resp)
        self.assertTrue(self.alarm_id in data['message'])
        self.assertTrue(self.alarm_id in data['details'])

    def test_reset_session(self):
        """
        Reset session, remove all objects
        """
        req = request(self, self.root, "GET", self.uri + '/entities')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['metadata']['count'], 1)

        req = request(self, self.root, "GET", self.uri + '/mimic/reset')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)

        req = request(self, self.root, "GET", self.uri + '/entities')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['metadata']['count'], 0)

    def test_unicode_label(self):
        """
        Create an entity with weird letters in the name.
        """
        req = request(self, self.root, "POST", self.uri + '/entities',
                      json.dumps({'label': u'\u0CA0_\u0CA0'}))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)

    def test_overview_pagination(self):
        """
        The overview call returns paginated results.
        """
        self.createEntity('entity-2')
        req = request(self, self.root, "GET", self.uri + '/views/overview?limit=1')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['values'][0]['entity']['label'], 'ItsAnEntity')

        req = request(self, self.root, "GET", self.uri +
                      '/views/overview?marker=' + data['metadata']['next_marker'])
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['values'][0]['entity']['label'], 'entity-2')

    def test_overview_pagination_marker_not_found(self):
        """
        If the pagination marker is not present in the entities list,
        the paginated overview call returns results from the beginning.
        """
        req = request(self, self.root, "GET", self.uri + '/views/overview?marker=enDoesNotExist')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        self.assertEquals(data['values'][0]['entity']['label'], 'ItsAnEntity')
