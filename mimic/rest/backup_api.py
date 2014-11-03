import json
from six import text_type
from zope.interface import implementer
from twisted.web.server import Request
from twisted.plugin import IPlugin
from mimic.rest.mimicapp import MimicApp
from mimic.imimic import IAPIMock
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.canned_responses.backup import list_agents
from uuid import uuid4

@implementer(IAPIMock, IPlugin)
class BackupApi(object):

    def catalog_entries(self, tenant_id):

        return [
            Entry(tenant_id, "rax:backup", "cloudBackup",
                  [
                      Endpoint(tenant_id, "ORD", text_type(uuid4()),
                               prefix="v2")
                  ])
        ]

    def resource_for_region(self, region, uri_prefix, session_store):

        return BackupApiRoutes(uri_prefix, session_store).app.resource()

class BackupApiRoutes(object):

    app = MimicApp() 

    def __init__(self, uri_prefix, session_store):

        self.uri_prefix = uri_prefix
        self._session_store = session_store

    @app.route('/v2/<string:tenant_id>/health', methods=['GET'])
    def get_health(self, request, tenant_id):

        pass

    @app.route('/v2/<string:tenant_id>/agents', methods=['GET'])
    def get_agents(self, request, tenant_id):

        response_data = list_agents(tenant_id)
        request.setResponseCode(response_data[1])

        return json.dumps(response_data[0])
