"""
MAAS Mock API
"""

import json,collections,time
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
    def __init__(self,regions=["ORD"]):
      self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Nova API.
        """
        return [
            Entry(
                tenant_id, "rax:monitor", "cloudMonitoring",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()), "v1.0") for region in self._regions
                ]
            )
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return MaasMock(self,uri_prefix,session_store,region).app.resource()


class E_Cache(dict):
  def __init__(self):
    self.json_home = json.loads(file('mimic/rest/cloudMonitoring_json_home.json').read()) 
    self.metrics_list = [] 
    self.entities_list = [] 
    self.checks_list = [] 
    self.alarms_list = [] 

def createEntity(params):
  import random,string
  params = collections.defaultdict(lambda:'',params)
  newentity = {}
  newentity['label'] =params[u'label'].encode("ascii")
  newentity['id'] = newentity['label']+''.join(random.sample(string.letters+string.digits,8))
  newentity['agent_id'] = params['agent_id'] or ''.join(random.sample(string.letters+string.digits,24))
  newentity['created_at'] = time.time()
  newentity['updated_at'] = time.time()
  newentity['managed'] = params['managed']
  newentity['metadata'] = params['metadata']
  newentity['ip_addresses'] = params['ip_addresses'] or {'access_ip0_v6':'2001:4800:7812:0514:6eaf:ff05:93d7',
                                                         'access_ip1_v4':'133.713.371.337',
                                                         'private0_v4':'10.177.177.12',
                                                         'public0_v6':'2001:4800:7812:0514:6eaf:ff05:93d7',
                                                         'public1_v4':'166.78.78.19' }
  return newentity

    
def createCheck(params):
  self.params = collections.defaultdict(lambda:'',params)

def createAlarm(params):
  self.params = collections.defaultdict(lambda:'',params)


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
      return ( self._session_store.session_for_tenant_id(tenant_id)
                .data_for_api(self._api_mock,lambda: collections.defaultdict(E_Cache))[self._name]
             )
      
    app = MimicApp()

    @app.route('/v1.0/<string:tenant_id>/entities', methods=['GET'])
    def list_entities(self, request, tenant_id):
      entities = self._entity_cache_for_tenant(tenant_id).entities_list
      metadata = {}
      metadata['count'] = len(entities)
      metadata['limit'] = 1000
      metadata['marker'] = None
      metadata['next_marker'] = None 
      metadata['next_href'] = None 
      request.setResponseCode(200)
      return json.dumps({'metadata':metadata,'values':entities})

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>', methods=['GET'])
    def get_entity(self, request, tenant_id,entity_id):
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

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>', methods=['DELETE'])
    def delete_entity(self, request, tenant_id,entity_id):
      for q in range(len(self._entity_cache_for_tenant(tenant_id).entities_list)):
        if self._entity_cache_for_tenant(tenant_id).entities_list[q]['id'] == entity_id:
          del self._entity_cache_for_tenant(tenant_id).entities_list[q]
          break
      request.setResponseCode(204)

    @app.route('/v1.0/<string:tenant_id>/entities/<string:entity_id>/checks', methods=['GET'])
    def get_checks_for_entity(self, request, tenant_id,entity_id):
      checks = []
      for c in self._entity_cache_for_tenant(tenant_id).checks_list:
        if c['entity_id'] == entity_id:
          checks.append(c)
      metadata = {}
      metadata['count'] = len(checks)
      metadata['limit'] = 1000
      metadata['marker'] = None
      metadata['next_marker'] = None 
      metadata['next_href'] = None 
      request.setResponseCode(200)
      return json.dumps({'metadata':metadata,'values':checks})
        
    @app.route('/v1.0/<string:tenant_id>/entities', methods=['POST'])
    def create_entity(self, request, tenant_id):
      postdata = json.loads(request.content.read())
      myhostname_and_port = 'http://'+request.getRequestHostname()+":8900"
      newentity = createEntity({'label':postdata[u'label'].encode('ascii')})
      self._entity_cache_for_tenant(tenant_id).entities_list.append(newentity)
      request.setResponseCode(201)
      request.setHeader('location',myhostname_and_port+request.path+'/'+newentity['id'])
      request.setHeader('x-object-id',newentity['id'])
      return ''  

    @app.route('/v1.0/<string:tenant_id>/views/overview', methods=['GET'])
    def overview(self, request, tenant_id):
      entities = self._entity_cache_for_tenant(tenant_id).entities_list
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
        v['checks'] = []
        v['entity'] = e 
        v['latest_alarm_states'] = []
        values.append(v)
      request.setResponseCode(200)
      return json.dumps({'metadata':metadata,'values':values})

    @app.route('/v1.0/<string:tenant_id>/__experiments/json_home', methods=['GET'])
    def service_json_home(self, request, tenant_id):
      import re
      cache = self._entity_cache_for_tenant(tenant_id)
      request.setResponseCode(200)
      myhostname_and_port = request.getRequestHostname()+":8900"
      mockapi_id = re.findall('/mimicking/(.+?)/',request.path)[0]
      return json.dumps(cache.json_home)\
        .replace('.com/v1.0','.com/mimicking/'+mockapi_id+'/ORD/v1.0')\
        .replace('monitoring.api.rackspacecloud.com',myhostname_and_port)\
        .replace("https://","http://")

    @app.route('/v1.0/<string:tenant_id>/views/agent_host_info', methods=['GET'])
    def view_agent_host_info(self, request, tenant_id):
      request.setResponseCode(400)
      return """{
        "type": "agentDoesNotExist",
        "code": 400,
        "message": "Agent does not exist",
        "details": "Agent c302622d-7612-4485-af8b-8363d8ce9184 does not exist.",
        "txnId": ".rh-quqy.h-ord1-maas-prod-api1.r-1wej75Ht.c-21273930.ts-1410911874749.v-858fee7"
      }"""

    @app.route('/v1.0/<string:tenant_id>/views/metric_list', methods=['GET'])
    def views_metric_list(self, request, tenant_id):
      metrics = self._entity_cache_for_tenant(tenant_id).metrics_list
      metadata = {}
      metadata['count'] = len(metrics)
      metadata['marker'] = None 
      metadata['next_marker'] = None 
      metadata['limit'] = 1000
      metadata['next_href'] = None 
      request.setResponseCode(200)
      return json.dumps({'metadata':metadata,'values':metrics})
       
    @app.route('/v1.0/<string:tenant_id>/__experiments/multiplot', methods=['POST'])
    def multiplot(self, request, tenant_id):
      metrics = self._entity_cache_for_tenant(tenant_id).metrics_list
      request.setResponseCode(200)
      return json.dumps({'metrics':metrics}) 
    

