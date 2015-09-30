import json
import treq
from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase
from mimic.model.maas_objects import Metric, CheckType
from mimic.rest.maas_api import MaasApi, MaasControlApi
from mimic.test.helpers import json_request, request
from mimic.test.fixtures import APIMockHelper


class MaasObjectsTests(SynchronousTestCase):
    """
    Tests for maas objects, cases that aren't hit by the broader API test.
    """
    def test_test_check_metric_unknown_type_value_errors(self):
        """
        Known types for TestCheckMetric are 'i', 'n', and 's'. Other types
        raise ValueError.
        """
        metric = Metric(name='whuut', type='z')
        with self.assertRaises(ValueError):
            metric.get_value_for_test_check(
                timestamp=0,
                entity_id='en123456',
                check_id='__test_check')

    def test_test_check_data_missing_metric_name_errors(self):
        """
        If you query a TestCheckData for a metric it doesn't have, you get
        NameError.
        """
        clock = Clock()
        check_type = CheckType(clock=clock, metrics=[
            Metric(name='that_metric', type='i', unit='count')])
        with self.assertRaises(NameError):
            check_type.get_metric_by_name('not_that_metric')


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
        req = request(self, self.root, "POST", self.uri + '/entities',
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        entity_id = resp.headers.getRawHeaders('x-object-id')[0]
        location = resp.headers.getRawHeaders('location')[0]
        self.assertEquals(location, self.uri + '/entities/' + entity_id)
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
        checks_endpoint = '{0}/entities/{1}/checks'.format(self.uri, entity_id)
        req = request(self, self.root, "POST", checks_endpoint,
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        check_id = resp.headers.getRawHeaders('x-object-id')[0]
        location = resp.headers.getRawHeaders('location')[0]
        self.assertEquals(location, checks_endpoint + '/' + check_id)
        return resp

    def createAlarm(self, label, entity_id, check_id):
        """
        Util function alarm
        """
        postdata = {}
        postdata['check_id'] = check_id
        postdata['label'] = label
        postdata['notification_plan_id'] = 'npTechnicalContactsEmail'
        alarms_endpoint = '{0}/entities/{1}/alarms'.format(self.uri, entity_id)
        req = request(self, self.root, "POST", alarms_endpoint,
                      json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        alarm_id = resp.headers.getRawHeaders('x-object-id')[0]
        location = resp.headers.getRawHeaders('location')[0]
        self.assertEquals(location, alarms_endpoint + '/' + alarm_id)
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
        nt_id = resp.headers.getRawHeaders('x-object-id')[0]
        location = resp.headers.getRawHeaders('location')[0]
        self.assertEquals(location, self.uri + '/notifications/' + nt_id)
        return resp

    def createNotificationPlan(self, label):
        """
        Util create notification plan
        """
        postdata = {'label': label}
        req = request(self, self.root, "POST", self.uri + '/notification_plans', json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        np_id = resp.headers.getRawHeaders('x-object-id')[0]
        location = resp.headers.getRawHeaders('location')[0]
        self.assertEquals(location, self.uri + '/notification_plans/' + np_id)
        return resp

    def createSuppression(self, label):
        postdata = {'label': label}
        req = request(self, self.root, "POST", self.uri + '/suppressions', json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 201)
        sp_id = resp.headers.getRawHeaders('x-object-id')[0]
        location = resp.headers.getRawHeaders('location')[0]
        self.assertEquals(location, self.uri + '/suppressions/' + sp_id)
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
        self.assertIsInstance(self.entity_id, str)
        self.assertTrue(self.entity_id.startswith('en'))
        self.assertIsInstance(self.check_id, str)
        self.assertTrue(self.check_id.startswith('ch'))
        self.assertIsInstance(self.alarm_id, str)
        self.assertTrue(self.alarm_id.startswith('al'))
        self.assertIsInstance(self.nt_id, str)
        self.assertTrue(self.nt_id.startswith('nt'))
        self.assertIsInstance(self.np_id, str)
        self.assertTrue(self.np_id.startswith('np'))
        self.assertIsInstance(self.sp_id, str)
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
        Attempting to get an entity with a nonexistent ID returns 404.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "GET", '{0}/entities/whatever'.format(self.uri)))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['type'], 'notFoundError')

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

    def test_get_missing_check_404s(self):
        """
        Trying to GET a nonexistent check causes a 404.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "GET", '{0}/entities/{1}/checks/Whut'.format(
                self.uri, self.entity_id)))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['type'], 'notFoundError')

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

    def test_create_check_missing_type_400s(self):
        """
        When trying to create a check and missing a `type` property,
        MaaS returns 400 Bad Request.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/entities/{1}/checks'.format(self.uri, self.entity_id),
                         json.dumps({'label': 'wow-check'})))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data['type'], 'badRequest')
        self.assertEquals(data['message'], 'Validation error for key \'type\'')

    def test_create_entity_with_unrecognized_keys(self):
        """
        When creating an entity with properties that are not
        recognized by MaaS, MaaS creates the entity and stores keys
        that it knows how to use.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST", '{0}/entities'.format(self.uri),
                    json.dumps({'label': 'foo', 'whut': 'WAT'})))
        self.assertEquals(resp.code, 201)

    def test_update_entity(self):
        """
        update entity
        """
        entity_endpoint = '{0}/entities/{1}'.format(self.uri, self.entity_id)
        req = request(self, self.root, "GET", entity_endpoint)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        data['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT", entity_endpoint, json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        self.assertEquals(entity_endpoint, resp.headers.getRawHeaders('location')[0])
        req = request(self, self.root, "GET", entity_endpoint)
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

    def test_create_alarm_missing_check_id_400s(self):
        """
        When trying to create an alarm and missing a `check_id` property,
        MaaS returns 400 Bad Request.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/entities/{1}/alarms'.format(self.uri, self.entity_id),
                         json.dumps({'label': 'wow-alarm',
                                     'notification_plan_id': self.np_id})))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data['type'], 'badRequest')
        self.assertEquals(data['message'], 'Validation error for key \'check_id\'')

    def test_create_alarm_missing_np_id_400s(self):
        """
        When trying to create an alarm and missing a `notification_plan_id`
        property, MaaS returns 400 Bad Request.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/entities/{1}/alarms'.format(self.uri, self.entity_id),
                         json.dumps({'label': 'wow-alarm',
                                     'check_id': self.check_id})))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data['type'], 'badRequest')
        self.assertEquals(data['message'], 'Validation error for key \'notification_plan_id\'')

    def test_update_check(self):
        """
        update check
        """
        check_endpoint = '{0}/entities/{1}/checks/{2}'.format(
            self.uri, self.entity_id, self.check_id)
        req = request(self, self.root, "GET", check_endpoint)
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        data = self.get_responsebody(resp)
        data['label'] = 'Iamamwhoami'
        req = request(self, self.root, "PUT", check_endpoint, json.dumps(data))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        self.assertEquals(check_endpoint, resp.headers.getRawHeaders('location')[0])
        req = request(self, self.root, "GET", check_endpoint)
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

    def test_create_check_with_unrecognized_keys(self):
        """
        When creating a check with properties that are not
        recognized by MaaS, MaaS creates the entity and stores keys
        that it knows how to use.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/entities/{1}/checks'.format(self.uri, self.entity_id),
                    json.dumps({'label': 'check-foo',
                                'type': 'remote.ping',
                                'whut': 'WAT'})))
        self.assertEquals(resp.code, 201)

    def test_update_alarm(self):
        """
        update alarm
        """
        req = request(self, self.root, "GET", self.uri + '/views/overview')
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 200)
        alarm = self.get_responsebody(resp)['values'][0]['alarms'][0]
        alarm['label'] = 'Iamamwhoami'
        alarm_endpoint = '{0}/entities/{1}/alarms/{2}'.format(
            self.uri, self.entity_id, self.alarm_id)
        req = request(self, self.root, "PUT", alarm_endpoint, json.dumps(alarm))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code, 204)
        self.assertEquals(alarm_endpoint, resp.headers.getRawHeaders('location')[0])
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

    def test_create_alarm_with_unrecognized_keys(self):
        """
        When creating an alarm with properties that are not
        recognized by MaaS, MaaS creates the entity and stores keys
        that it knows how to use.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/entities/{1}/alarms'.format(self.uri, self.entity_id),
                    json.dumps({'label': 'alarm-foo',
                                'check_id': self.check_id,
                                'criteria': 'return new AlarmStatus(OK);',
                                'notification_plan_id': 'npL01Wu7',
                                'whut': 'WAT'})))
        self.assertEquals(resp.code, 201)

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

    def test_delete_nonexistent_alarm_404s(self):
        """
        Deleting an alarm that does not exist causes a 404.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "DELETE",
                         '{0}/entities/{1}/alarms/alWhut'.format(self.uri, self.entity_id)))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['details'],
                          'Object "Alarm" with key "{0}:alWhut" does not exist'.format(self.entity_id))

    def test_test_check(self):
        """
        The test-check API should return fake test-check results.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-check',
                         json.dumps({'type': 'agent.disk'})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(1, len(data))
        self.assertIn('read_bytes', data[0]['metrics'])

    def test_test_check_setting_available(self):
        """
        The test-check control API can set available=False.
        """
        resp = self.successResultOf(request(self, self.root, "PUT",
                                    '{0}/entities/{1}/checks/test_responses/{2}'.format(
                                        self.ctl_uri, self.entity_id, 'agent.load_average'),
                                    json.dumps([{'available': False}])))
        self.assertEquals(resp.code, 204)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-check',
                         json.dumps({'type': 'agent.load_average'})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(False, data[0]['available'])

    def test_test_check_setting_status(self):
        """
        The test-check control API can set the status message.
        """
        resp = self.successResultOf(request(self, self.root, "PUT",
                                    '{0}/entities/{1}/checks/test_responses/{2}'.format(
                                        self.ctl_uri, self.entity_id, 'agent.memory'),
                                    json.dumps([{'status': 'whuuut'}])))
        self.assertEquals(resp.code, 204)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-check',
                         json.dumps({'type': 'agent.memory'})))
        self.assertEquals(resp.code, 200)
        self.assertEquals('whuuut', data[0]['status'])

    def test_test_check_setting_metrics(self):
        """
        The test-check control API can set metrics.

        Subsequent requests to set the same metrics on the same check type
        for the same entity will override.
        """
        resp = self.successResultOf(request(self, self.root, "PUT",
                                    '{0}/entities/{1}/checks/test_responses/{2}'.format(
                                        self.ctl_uri, self.entity_id, 'remote.http'),
                                    json.dumps([{'metrics': {'duration': {'data': 123}},
                                                 'monitoring_zone_id': 'mzdfw'}])))
        self.assertEquals(resp.code, 204)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-check',
                         json.dumps({'type': 'remote.http',
                                     'monitoring_zones_poll': ['mzdfw']})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(123, data[0]['metrics']['duration']['data'])

        resp = self.successResultOf(request(self, self.root, "PUT",
                                    '{0}/entities/{1}/checks/test_responses/{2}'.format(
                                        self.ctl_uri, self.entity_id, 'remote.http'),
                                    json.dumps([{'metrics': {'duration': {'data': 456}},
                                                 'monitoring_zone_id': 'mzdfw'}])))
        self.assertEquals(resp.code, 204)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-check',
                         json.dumps({'type': 'remote.http',
                                     'monitoring_zones_poll': ['mzdfw']})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(456, data[0]['metrics']['duration']['data'])

    def test_test_check_clears_metrics(self):
        """
        The test-check control API can clear metrics.

        ..note: Randomly generated string metrics are between 12 and 30
        characters long.
        """
        options = {'data': 'really great forty-three character sentence'}

        resp = self.successResultOf(
            request(self, self.root, "PUT",
                    '{0}/entities/{1}/checks/test_responses/{2}'.format(
                        self.ctl_uri, self.entity_id, 'agent.filesystem'),
                    json.dumps([{'metrics': {'options': options}}])))
        self.assertEquals(resp.code, 204)

        resp = self.successResultOf(
            request(self, self.root, "DELETE",
                    '{0}/entities/{1}/checks/test_responses/{2}'.format(
                        self.ctl_uri, self.entity_id, 'agent.filesystem')))
        self.assertEquals(resp.code, 204)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-check',
                         json.dumps({'type': 'agent.filesystem'})))
        self.assertEquals(resp.code, 200)
        self.assertTrue(len(data[0]['metrics']['options']['data']) < 43)

    def test_test_check_empty_clear_does_nothing(self):
        """
        If the user sends a DELETE request to the test_responses control API
        and no control override is in place, nothing happens.
        """
        resp = self.successResultOf(
            request(self, self.root, "DELETE",
                    '{0}/entities/{1}/checks/test_responses/{2}'.format(
                        self.ctl_uri, self.entity_id, 'agent.network')))
        self.assertEquals(resp.code, 204)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-check',
                         json.dumps({'type': 'agent.network'})))
        self.assertEquals(resp.code, 200)
        self.assertIsInstance(data[0]['metrics']['rx_bytes']['data'], int)

    def test_test_check_other_types(self):
        """
        The test-check API defines responses for a variety of check types.
        """
        for check_type in ['remote.http', 'remote.ping']:
            (resp, data) = self.successResultOf(
                json_request(self, self.root, "POST",
                             '{0}/entities/{1}/test-check'.format(self.uri, self.entity_id),
                             json.dumps({'type': check_type})))
            self.assertEquals(resp.code, 200)
            self.assertEquals(1, len(data))
            self.assertTrue('metrics' in data[0])

    def test_test_alarm(self):
        """
        Test test-alarm API in normal operation.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-alarm',
                         json.dumps({'criteria': 'return new AlarmStatus(OK);',
                                     'check_data': [{}]})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(1, len(data))
        self.assertIn('state', data[0])
        self.assertIn('status', data[0])
        self.assertIn('timestamp', data[0])

    def test_test_alarm_setting_state(self):
        """
        Test test-alarm API setting the state parameter.
        """
        resp = self.successResultOf(request(self, self.root, "PUT",
                                            '{0}/entities/{1}/alarms/test_response'.format(
                                                self.ctl_uri, self.entity_id),
                                            json.dumps([{'state': 'OK'}])))
        self.assertEquals(resp.code, 204)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-alarm',
                         json.dumps({'criteria': 'return new AlarmStatus(OK);',
                                     'check_data': [{}]})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(1, len(data))
        self.assertEquals('OK', data[0]['state'])
        self.assertIn('timestamp', data[0])

    def test_test_alarm_setting_status(self):
        """
        Users can set the status field on the response from the test-alarm API.
        """
        resp = self.successResultOf(
            request(self, self.root, "PUT",
                    '{0}/entities/{1}/alarms/test_response'.format(
                        self.ctl_uri, self.entity_id),
                    json.dumps([{'state': 'OK',
                                 'status': 'test status message'}])))
        self.assertEquals(resp.code, 204)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-alarm',
                         json.dumps({'criteria': 'return new AlarmStatus(OK);',
                                     'check_data': [{}]})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(1, len(data))
        self.assertEquals('test status message', data[0]['status'])

    def test_test_alarm_clearing_response(self):
        """
        Sending HTTP DELETE to the entity's test-alarm response
        causes the response to be cleared and not returned later.
        """
        resp = self.successResultOf(
            request(self, self.root, "PUT",
                    '{0}/entities/{1}/alarms/test_response'.format(
                        self.ctl_uri, self.entity_id),
                    json.dumps([{'state': 'OK',
                                 'status': 'test-alarm working OK'}])))
        self.assertEquals(resp.code, 204)

        resp = self.successResultOf(request(self, self.root, "DELETE",
                                            '{0}/entities/{1}/alarms/test_response'.format(
                                                self.ctl_uri, self.entity_id)))
        self.assertEquals(resp.code, 204)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         self.uri + '/entities/' + self.entity_id + '/test-alarm',
                         json.dumps({'criteria': 'return new AlarmStatus(OK);',
                                     'check_data': [{}]})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(1, len(data))
        self.assertNotEquals('test-alarm working OK', data[0]['status'])

    def test_test_alarm_setting_errors(self):
        """
        Users can use the control API to make the test-alarm API return errors.
        """
        parse_error = {'code': 400,
                       'type': 'alarmParseError',
                       'message': 'Failed to parse alarm'}
        not_found_error = {'code': 404,
                           'type': 'notFoundError',
                           'message': 'Object does not exist'}

        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/entities/{1}/alarms/test_errors'.format(
                        self.ctl_uri, self.entity_id),
                    json.dumps({'code': 400, 'response': parse_error})))
        self.assertEquals(resp.code, 201)

        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/entities/{1}/alarms/test_errors'.format(
                        self.ctl_uri, self.entity_id),
                    json.dumps({'code': 404, 'response': not_found_error})))
        self.assertEquals(resp.code, 201)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/entities/{1}/test-alarm'.format(self.uri, self.entity_id),
                         json.dumps({'criteria': 'return new AlarmStatus(OK);',
                                     'check_data': [{}]})))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data, parse_error)

        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/entities/{1}/test-alarm'.format(self.uri, self.entity_id),
                         json.dumps({'criteria': 'return new AlarmStatus(OK);',
                                     'check_data': [{}]})))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data, not_found_error)

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

    def test_delete_nonexistent_check_404s(self):
        """
        Deleting a check that does not exist causes a 404.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "DELETE",
                         '{0}/entities/{1}/checks/chWhut'.format(self.uri, self.entity_id)))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['details'],
                          'Object "Check" with key "{0}:chWhut" does not exist'.format(self.entity_id))

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

    def test_delete_nonexistent_entity_404s(self):
        """
        Deleting an entity that does not exist causes a 404.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "DELETE", '{0}/entities/whut'.format(self.uri)))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['details'], 'Object "Entity" with key "whut" does not exist')

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

    def test_create_notification_plan_with_unrecognized_keys(self):
        """
        When creating a notification plan with properties that are not
        recognized by MaaS, MaaS creates the entity and stores keys
        that it knows how to use.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/notification_plans'.format(self.uri),
                    json.dumps({'label': 'np-foo',
                                'whut': 'WAT'})))
        self.assertEquals(resp.code, 201)

    def test_create_notification_with_unrecognized_keys(self):
        """
        When creating a notification with properties that are not
        recognized by MaaS, MaaS creates the entity and stores keys
        that it knows how to use.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/notifications'.format(self.uri),
                    json.dumps({'label': 'nt-foo',
                                'details': {'address': 'bob@company.com'},
                                'type': 'email',
                                'whut': 'WAT'})))
        self.assertEquals(resp.code, 201)

    def test_create_suppression_with_unrecognized_keys(self):
        """
        When creating a suppression with properties that are not
        recognized by MaaS, MaaS creates the entity and stores keys
        that it knows how to use.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/suppressions'.format(self.uri),
                    json.dumps({'label': 'sp-foo',
                                'whut': 'WAT'})))
        self.assertEquals(resp.code, 201)

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

    def test_unknown_check_type_returns_empty_metrics_list(self):
        """
        A check type that Mimic doesn't know about causes the list
        of metrics on that check to be empty.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/entities/{1}/checks'.format(self.uri, self.entity_id),
                    json.dumps({'type': 'agent.chupacabra'})))
        self.assertEquals(resp.code, 201)
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "GET", '{0}/views/metric_list'.format(self.uri)))
        self.assertEquals(resp.code, 200)
        chupacabra_check = [check for check in data['values'][0]['checks']
                            if check['type'] == 'agent.chupacabra']
        self.assertEquals(chupacabra_check[0]['metrics'], [])

    def test_metrics_list_agent_check(self):
        """
        A known agent check type returns appropriate metrics for
        that check type.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/entities/{1}/checks'.format(self.uri, self.entity_id),
                    json.dumps({'type': 'agent.cpu'})))
        self.assertEquals(resp.code, 201)
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "GET", '{0}/views/metric_list'.format(self.uri)))
        self.assertEquals(resp.code, 200)
        cpu_check = [check for check in data['values'][0]['checks']
                     if check['type'] == 'agent.cpu']
        self.assertEquals(cpu_check[0]['metrics'][0]['name'], 'user_percent_average')

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

    def test_multiplot_missing_check_returns_400(self):
        """
        When POSTing to /__experiments/multiplot and the check does not
        exist, the MaaS API returns a 400.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/__experiments/multiplot?from={1}&to={2}&points={3}'.format(
                             self.uri, '1412902262560', '1412988662560', 500),
                         json.dumps({'metrics': [{'entity_id': self.entity_id,
                                                  'check_id': 'bogus',
                                                  'metric': 'mzord.available'}]})))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data['type'], 'requiredNotFoundError')

    def test_multiplot_unknown_check_type(self):
        """
        Creating a check with a type unknown to Mimic causes an unknown
        metric and empty data to be returned.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/entities/{1}/checks'.format(self.uri, self.entity_id),
                    json.dumps({'type': 'agent.whatever'})))
        self.assertEquals(resp.code, 201)
        check_id = resp.headers.getRawHeaders('x-object-id')[0]
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/__experiments/multiplot?from={1}&to={2}&points={3}'.format(
                             self.uri, '1412902262560', '1412988662560', 500),
                         json.dumps({'metrics': [{'entity_id': self.entity_id,
                                                  'check_id': check_id,
                                                  'metric': 'whut'}]})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['metrics'][0]['type'], 'unknown')
        self.assertEquals(len(data['metrics'][0]['data']), 0)

    def test_multiplot_malformatted_remote_metric(self):
        """
        Multiplot metrics for remote checks must stuff the monitoring
        zone in the front of the metric name, e.g., mzord.duration.
        Requesting an incorrectly formatted metric name causes an unknown
        metric and empty data to be returned.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/__experiments/multiplot?from={1}&to={2}&points={3}'.format(
                             self.uri, '1412902262560', '1412988662560', 500),
                         json.dumps({'metrics': [{'entity_id': self.entity_id,
                                                  'check_id': self.check_id,
                                                  'metric': 'LOLWUT'}]})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['metrics'][0]['type'], 'unknown')
        self.assertEquals(len(data['metrics'][0]['data']), 0)

    def test_multiplot_nonexistent_metric(self):
        """
        Getting multiplot metrics that Mimic doesn't know about cause
        an unknown metric and empty data to be returned, if the check
        type is one that Mimic knows about.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/__experiments/multiplot?from={1}&to={2}&points={3}'.format(
                             self.uri, '1412902262560', '1412988662560', 500),
                         json.dumps({'metrics': [{'entity_id': self.entity_id,
                                                  'check_id': self.check_id,
                                                  'metric': 'mzord.nonexistent'}]})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['metrics'][0]['type'], 'unknown')
        self.assertEquals(len(data['metrics'][0]['data']), 0)

    def test_multiplot_single_point(self):
        """
        Plotting a single point should not cause a server error.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/__experiments/multiplot?from={1}&to={2}&points={3}'.format(
                        self.uri, '1412902262560', '1412988662560', 1),
                    json.dumps({'metrics': [{'entity_id': self.entity_id,
                                             'check_id': self.check_id,
                                             'metric': 'mzord.available'}]})))
        self.assertEquals(resp.code, 200)

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
        self.assertIsNot(None, mynt)
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

    def test_delete_nonexistent_notification_404s(self):
        """
        Deleting a notification that does not exist causes a 404.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "DELETE", '{0}/notifications/ntWhut'.format(self.uri)))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['details'], 'Object "Notification" with key "ntWhut" does not exist')

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

    def test_delete_nonexistent_notification_plan_404s(self):
        """
        Deleting a notification plan that does not exist causes a 404.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "DELETE", '{0}/notification_plans/npWhut'.format(self.uri)))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['details'], 'Object "NotificationPlan" with key "npWhut" does not exist')

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

    def test_delete_nonexistent_suppression_404s(self):
        """
        Deleting a suppression that does not exist causes a 404.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "DELETE", '{0}/suppressions/spWhut'.format(self.uri)))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['details'], 'Object "Suppression" with key "spWhut" does not exist')

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

    def test_overview_filters_by_entity(self):
        """
        The overview call restricts results to the desired entity,
        regardless if other entities exist.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "GET",
                         '{0}/views/overview?entityId={1}'.format(
                             self.uri, self.entity_id)))
        self.assertEquals(resp.code, 200)
        self.assertEquals(len(data['values']), 1)
        self.assertEquals(data['values'][0]['entity']['label'], 'ItsAnEntity')

    def test_overview_missing_entity_404s(self):
        """
        If the user passes in a non-existing entity ID, a 404 is returned.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "GET",
                         '{0}/views/overview?entityId={1}'.format(
                             self.uri, 'enDoesNotExist')))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['type'], 'notFoundError')

    def test_latest_alarm_states(self):
        """
        The /views/latest_alarm_states API recalls alarm states that were stored
        using the control API.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/entities/{1}/alarms/{2}/states'.format(
                        self.ctl_uri, self.entity_id, self.alarm_id),
                    json.dumps({'state': 'CRITICAL',
                                'analyzed_by_monitoring_zone_id': 'mzVegetaScouter',
                                'status': 'It\'s OVER... NINE... THOUSAND!!1'})))
        self.assertEquals(resp.code, 201)
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "GET", '{0}/views/latest_alarm_states'.format(self.uri)))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['values'][0]['latest_alarm_states'][0]['state'], 'CRITICAL')

    def test_alarm_states_same_alarm_gets_previous_state(self):
        """
        When setting a new alarm state on the same entity and same alarm ID,
        the previous state is set correctly.
        """
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/entities/{1}/alarms/{2}/states'.format(
                        self.ctl_uri, self.entity_id, self.alarm_id),
                    json.dumps({'state': 'CRITICAL',
                                'analyzed_by_monitoring_zone_id': 'mzVegetaScouter',
                                'status': 'It\'s OVER... NINE... THOUSAND!!1'})))
        self.assertEquals(resp.code, 201)
        resp = self.successResultOf(
            request(self, self.root, "POST",
                    '{0}/entities/{1}/alarms/{2}/states'.format(
                        self.ctl_uri, self.entity_id, self.alarm_id),
                    json.dumps({'state': 'OK',
                                'status': 'Meh'})))
        self.assertEquals(resp.code, 201)
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "GET", '{0}/views/latest_alarm_states'.format(self.uri)))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['values'][0]['latest_alarm_states'][0]['previous_state'], 'CRITICAL')

    def test_create_alarm_state_missing_alarm_404s(self):
        """
        If the user tries to create an alarm state on an alarm that doesn't exist,
        Mimic returns a 404.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/entities/{1}/alarms/{2}/states'.format(
                             self.ctl_uri, self.entity_id, 'alDoesNotExist'),
                         json.dumps({'state': 'OK', 'status': 'bogus'})))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['type'], 'notFoundError')

    def test_create_alarm_state_missing_state_400s(self):
        """
        If the user tries to create an alarm state without a `state` parameter,
        Mimic returns 400 Bad Request.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/entities/{1}/alarms/{2}/states'.format(
                             self.ctl_uri, self.entity_id, self.alarm_id),
                         json.dumps({'status': 'This wont work'})))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data['type'], 'badRequest')
        self.assertEquals(data['details'], 'Missing required key (state)')

    def test_create_alarm_state_missing_status_400s(self):
        """
        If the user tries to create an alarm state without a `status` parameter,
        Mimic returns 400 Bad Request.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/entities/{1}/alarms/{2}/states'.format(
                             self.ctl_uri, self.entity_id, self.alarm_id),
                         json.dumps({'state': 'WARNING'})))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data['type'], 'badRequest')
        self.assertEquals(data['details'], 'Missing required key (status)')

    def test_set_overrides_missing_check(self):
        """
        Trying to set the overrides on a check that does not exist causes a 404.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "PUT",
                         '{0}/entities/{1}/checks/chWhut/metrics/available'.format(
                             self.ctl_uri, self.entity_id),
                         json.dumps({'type': 'squarewave'})))
        self.assertEquals(resp.code, 404)
        self.assertEquals(data['type'], 'notFoundError')
        self.assertEquals(data['details'], ('Object "Check" with key ' +
                                            '"{0}:chWhut" does not exist'.format(self.entity_id)))

    def test_set_overrides_unknown_type(self):
        """
        Trying to set the overrides using an unknown metric type
        causes a 400 Bad Request response.
        """
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "PUT",
                         '{0}/entities/{1}/checks/{2}/metrics/available'.format(
                             self.ctl_uri, self.entity_id, self.check_id),
                         json.dumps({'type': 'lolwut'})))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data['type'], 'badRequest')
        self.assertEquals(data['details'], 'Unknown value for "type": "lolwut"')

    def test_set_overrides_squarewave(self):
        """
        Users can override metrics using a square wave function.
        """
        resp = self.successResultOf(
            request(self, self.root, "PUT",
                    '{0}/entities/{1}/checks/{2}/metrics/available'.format(
                        self.ctl_uri, self.entity_id, self.check_id),
                    json.dumps({'type': 'squarewave',
                                'options': {'min': 11,
                                            'max': 22,
                                            'offset': 0,
                                            'period': 100},
                                'monitoring_zones': ['mzord']})))
        self.assertEquals(resp.code, 204)
        (resp, data) = self.successResultOf(
            json_request(self, self.root, "POST",
                         '{0}/__experiments/multiplot?from=1&to=99&points=2'.format(self.uri),
                         json.dumps({'metrics': [{'entity_id': self.entity_id,
                                                  'check_id': self.check_id,
                                                  'metric': 'mzord.available'}]})))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['metrics'][0]['data'][0]['average'], 11)
        self.assertEquals(data['metrics'][0]['data'][1]['average'], 22)
