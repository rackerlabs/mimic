"""
MAAS Mock API
"""

import json
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

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Nova API.
        """
        return [
            Entry(
                tenant_id, "rax:monitor", "cloudMonitoring",
                [
                    Endpoint(tenant_id, "ORD", text_type(uuid4()), "v1.0")
                ]
            )
        ]

    def resource_for_region(self, uri_prefix):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return MaasMock(uri_prefix).app.resource()


class MaasMock(object):
    """
    Klein routes for the Monitoring API.
    """

    def __init__(self, uri_prefix):
        """
        Create a maas region with a given URI prefix (used for generating URIs
        to servers).
        """
        self.uri_prefix = uri_prefix

    app = MimicApp()

    @app.route('/v1.0/<string:tenant_id>/entities', methods=['GET'])
    def list_entities(self, request, tenant_id):
        """
        Returns a list of entities with Response code 200.
        """
        request.setResponseCode(200)
        return json.dumps({"entities": []})

    @app.route('/v1.0/<string:tenant_id>/__experiments/json_home', methods=['GET'])
    def service_json_home(self, request, tenant_id):
      request.setResponseCode(200)
      return file('mimic/rest/cloudMonitoring_json_home.json').read()

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
      request.setResponseCode(200)
      return file('mimic/rest/metric_list.json').read()
           
    @app.route('/v1.0/<string:tenant_id>/__experiments/multiplot', methods=['POST'])
    def multiplot(self, request, tenant_id):
      request.setResponseCode(200)
      return file('mimic/rest/multiplot.json').read()


