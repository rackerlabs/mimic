import json,treq
from twisted.trial.unittest import SynchronousTestCase
from mimic.rest.maas_api import MaasApi
from mimic.test.helpers import json_request, request
from mimic.test.fixtures import APIMockHelper

class MaasAPITests(SynchronousTestCase):
    """
    Tests for maas plugin API
    """
    def createEntity(self, label):
        postdata = {}
        postdata['agent_id'] = None
        postdata['label'] = 'testCreateEntity'
        req = request(self, self.root, "POST", self.uri+'/entities', json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code,201)
        return resp

    def createCheck(self, label, entity_id):
        postdata = {}
        postdata['label'] = label
        postdata['details'] = {} 
        postdata['monitoring_zones_poll'] = ['mzdfw','mzord','mzlon']
        postdata['target_alias'] = 'public1_v4'
        postdata['target_hostname'] = None 
        postdata['target_resolver'] = None
        postdata['type'] = 'remote.ping' 
        req = request(self, self.root, "POST", self.uri+'/entities/'+entity_id+'/checks',
              json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code,201)
        return resp

    def createAlarm(self,label,entity_id,check_id):
        postdata = {}
        postdata['check_id'] = check_id
        postdata['entityId'] = entity_id
        postdata['label'] = label
        postdata['notification_plan_id'] = 'npTechnicalContactsEmail'
        req = request(self, self.root, "POST", 
        self.uri+'/entities/'+entity_id+'/alarms', json.dumps(postdata))
        resp = self.successResultOf(req)
        self.assertEquals(resp.code,201)
        return resp

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

        resp = self.createEntity('E')
        for h in resp.headers.getAllRawHeaders():
            if h[0].lower() == 'x-object-id':
                entity_id = h[1][0]
                break
        resp = self.createCheck('C',entity_id)
        for h in resp.headers.getAllRawHeaders():
            if h[0].lower() == 'x-object-id':
                check_id = h[1][0]
                break
        resp = self.createAlarm('A',entity_id,check_id)
        for h in resp.headers.getAllRawHeaders():
            if h[0].lower() == 'x-object-id':
                alarm_id = h[1][0]
                break

    def test_list__entity(self):
        """
        list entity
        """
        pass

        
