"""
Defines get token from Auth and create, delete, get servers and get images and flavors.
"""
import json
from twisted.web.server import Request

from mimic.json_schema.auth_schema import (get_token, get_user, get_user_token)
from mimic.json_schema.canned_responses import (get_server,
                                                create_server_example,
                                                get_image, get_flavor)
from mimic.rest.mimicapp import MimicApp

Request.defaultContentType = 'application/json'


class Mimic(object):

    """
    Rest endpoints for mocked Auth.
    """
    app = MimicApp()

    @app.route('/v2.0/tokens', methods=['POST'])
    def get_service_catalog_and_token(self, request):
        """
        Return a service catalog consisting of nova and load balancer mocked
        endpoints and an api token.
        """
        request.setResponseCode(200)
        return json.dumps(get_token)

    @app.route('/v1.1/mosso/<string:tenant_id>', methods=['GET'])
    def get_username(self, request, tenant_id):
        """
        Returns response with username 'autoscaleprod.
        """
        request.setResponseCode(301)
        return json.dumps(get_user())

    @app.route('/v2.0/RAX-AUTH/impersonation-tokens', methods=['POST'])
    def get_user_token(self, request):
        """
        Return a token id with expiration.
        """
        request.setResponseCode(200)
        content = json.loads(request.content.read())
        expires_in = content['RAX-AUTH:impersonation']['expire-in-seconds']
        return json.dumps(get_user_token(expires_in))

    @app.route('/v2/<string:tenant_id>/servers', methods=['POST'])
    def create_server(self, request, tenant_id):
        """
        Returns a generic get server response, with status 'ACTIVE'
        """
        request.setResponseCode(202)
        return json.dumps(create_server_example(tenant_id))

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>', methods=['GET'])
    def get_server(self, request, tenant_id, server_id):
        """
        Returns a generic get server response, with status 'ACTIVE'
        """
        request.setResponseCode(200)
        return json.dumps(get_server(server_id))

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>', methods=['DELETE'])
    def delete_server(self, request, tenant_id, server_id):
        """
        Returns a 204 response code, for any server id'
        """
        return request.setResponseCode(204)

    @app.route('/v2/<string:tenant_id>/images/<string:image_id>', methods=['GET'])
    def get_image(self, request, tenant_id, image_id):
        """
        Returns a get image response, for any given imageid
        """
        request.setResponseCode(200)
        return json.dumps(get_image(image_id))

    @app.route('/v2/<string:tenant_id>/flavors/<string:flavor_id>', methods=['GET'])
    def get_flavor(self, request, tenant_id, flavor_id):
        """
        Returns a get flavor response, for any given flavorid
        """
        request.setResponseCode(200)
        return json.dumps(get_flavor(flavor_id))
