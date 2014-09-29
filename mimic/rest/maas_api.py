"""
MAAS Mock API
"""

import json,collections
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
    self.overview_dictionary = json.loads(file('mimic/rest/overview_response.json').read())
    self.entities_dictionary = json.loads(file('mimic/rest/entities_response.json').read())
    self.metrics_dictionary = json.loads(file('mimic/rest/metric_list.json').read())
    self.multiplot_dictionary = json.loads(file('mimic/rest/multiplot.json').read())


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
      cache = self._session_store.session_for_tenant_id(tenant_id).data_for_api(self._api_mock,lambda: collections.defaultdict(E_Cache))[self._name]
      request.setResponseCode(200)
      return json.dumps(cache.entities_dictionary)
        
    @app.route('/v1.0/<string:tenant_id>/entities', methods=['POST'])
    def create_entity(self, request, tenant_id):
      import random,string
      request.setResponseCode(201)
      postdata = json.loads(request.content.read())
      myhostname_and_port = 'http://'+request.getRequestHostname()+":8900"
      entityid = postdata[u'label'].encode("ascii")+''.join(random.sample(string.letters+string.digits,8))
      request.setHeader('location',myhostname_and_port+request.path+'/'+entityid)
      request.setHeader('x-object-id',entityid)
      return ' '  

    @app.route('/v1.0/<string:tenant_id>/views/overview', methods=['GET'])
    def overview(self, request, tenant_id):
        cache = self._session_store.session_for_tenant_id(tenant_id).data_for_api(self._api_mock,lambda: collections.defaultdict(E_Cache))[self._name]
        request.setResponseCode(200)
        return json.dumps(cache.overview_dictionary)

    @app.route('/v1.0/<string:tenant_id>/__experiments/json_home', methods=['GET'])
    def service_json_home(self, request, tenant_id):
      import re
      cache = self._session_store.session_for_tenant_id(tenant_id).data_for_api(self._api_mock,lambda: collections.defaultdict(E_Cache))[self._name]
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
      cache = self._session_store.session_for_tenant_id(tenant_id).data_for_api(self._api_mock,lambda: collections.defaultdict(E_Cache))[self._name]
      request.setResponseCode(200)
      return json.dumps(cache.metrics_dictionary) 
       
    @app.route('/v1.0/<string:tenant_id>/__experiments/multiplot', methods=['POST'])
    def multiplot(self, request, tenant_id):
      cache = self._session_store.session_for_tenant_id(tenant_id).data_for_api(self._api_mock,lambda: collections.defaultdict(E_Cache))[self._name]
      request.setResponseCode(200)
      return json.dumps(cache.multiplot_dictionary) 

    

