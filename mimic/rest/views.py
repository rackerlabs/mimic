"""
Defines get token from Auth and create, delete, get servers and get images and flavors.
"""
from twisted.python import log

import json

from twisted.web.server import Request

from mimic.canned_responses.auth import (get_token, get_user,
                                         get_user_token, get_endpoints)
from mimic.canned_responses.nova import (get_server, get_limit,
                                         create_server_example,
                                         get_image, get_flavor)
from mimic.rest.mimicapp import MimicApp

Request.defaultContentType = 'application/json'


class Mimic(object):

    """
    Rest endpoints for mocked Auth.
    """
    app = MimicApp()
    s_cache = {}

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

    @app.route('/v2.0/tokens/<string:token_id>/endpoints', methods=['GET'])
    def get_service_catalog(self, request, token_id):
        """
        Return a service catalog consisting of nova and load balancer mocked
        endpoints.
        """
        request.setResponseCode(200)
        return json.dumps(get_endpoints())

    @app.route('/v2/<string:tenant_id>/servers', methods=['POST'])
    def create_server(self, request, tenant_id):
        """
        Returns a generic create server response, with status 'ACTIVE'.
        """
        request.setResponseCode(202)
        content = json.loads(request.content.read())
        response = create_server_example(tenant_id)
        self.s_cache[response['server']['id']] = content['server']
        self.s_cache[response['server']['id']].update(id=response['server']['id'])
        log.msg(self.s_cache)
        return json.dumps(response)

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>', methods=['GET'])
    def get_server(self, request, tenant_id, server_id):
        """
        Returns a generic get server response, with status 'ACTIVE'
        """
        if self.s_cache.get(server_id):
            request.setResponseCode(200)
            return json.dumps(get_server(tenant_id, server_id))
        else:
            return request.setResponseCode(404)

    @app.route('/v2/<string:tenant_id>/servers', methods=['GET'])
    def list_servers(self, request, tenant_id):
        """
        Returns number of servers that were created by the mocks, with the given name.
        """
        if 'name' in request.args:
            server_name = request.args['name'][0]
            log.msg(server_name)

        servers_list = [value for value in self.s_cache.values() if server_name in value['name']]
        log.msg(servers_list)
        request.setResponseCode(200)
        return json.dumps({'servers': servers_list})

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>', methods=['DELETE'])
    def delete_server(self, request, tenant_id, server_id):
        """
        Returns a 204 response code, for any server id'
        """
        if server_id in self.s_cache:
            del self.s_cache[server_id]
            log.msg(self.s_cache)
            return request.setResponseCode(204)
        else:
            return request.setResponseCode(404)

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

    @app.route('/v2/<string:tenant_id>/limits', methods=['GET'])
    def get_limit(self, request, tenant_id):
        """
        Returns a get flavor response, for any given flavorid
        """
        request.setResponseCode(200)
        return json.dumps(get_limit())
