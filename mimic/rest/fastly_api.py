# -*- test-case-name: mimic.test.test_auth -*-
"""
Defines get current customer
"""

import json

from twisted.web.server import Request

from mimic.rest.mimicapp import MimicApp
from mimic.canned_responses import fastly

Request.defaultContentType = 'application/json'


class FastlyApi(object):
    """
    Rest endpoints for mocked Fastly api.
    """

    app = MimicApp()

    def __init__(self, core):
        """
        :param MimicCore core: The core to which this FastlyApi will be
            communicating.
        """
        self.core = core
        self.services = {}
        self.fastly_response = fastly.FastlyResponse()

    @app.route('/current_customer', methods=['GET'])
    def get_current_customer(self, request):
        """
        Returns response with current customer details.
        """
        response = self.fastly_response.get_current_customer(request)
        return json.dumps(response)

    @app.route('/service', methods=['POST'])
    def create_service(self, request):
        """
        Returns POST Service.
        """
        url_data = request.args.items()
        response = self.fastly_response.create_service(request, url_data)
        return json.dumps(response)

    @app.route('/service/<string:service_id>/version', methods=['POST'])
    def create_version(self, request, service_id):
        """
        Returns POST Service.
        """
        response = self.fastly_response.create_version(request, service_id)
        return json.dumps(response)

    @app.route('/service/search', methods=['GET'])
    def get_service_by_name(self, request):
        """
        Returns response with current customer details.
        """
        url_data = request.args.items()
        data = dict((key, value) for key, value in url_data)
        service_name = data['name'][0]

        response = self.fastly_response.get_service_by_name(request,
                                                            service_name)
        return json.dumps(response)

    @app.route(
        '/service/<string:service_id>/version/<string:version_id>/domain',
        methods=['POST'])
    def create_domain(self, request, service_id, version_id):
        """
        Returns Create Domain Response.
        """
        response = self.fastly_response.create_domain(request,
                                                      service_id, version_id)
        return json.dumps(response)

    @app.route(
        '/service/<string:service_id>/version/<string:version_id>/domain/'
        'check_all',
        methods=['GET'])
    def check_domains(self, request, service_id, version_id):
        """
        Returns Check Domain.
        """
        response = self.fastly_response.check_domains(request,
                                                      service_id, version_id)
        return json.dumps(response)

    @app.route(
        '/service/<string:service_id>/version/<string:version_id>/backend',
        methods=['POST'])
    def create_backend(self, request, service_id, version_id):
        """
        Returns Create Backend Response.
        """
        response = self.fastly_response.create_backend(request,
                                                       service_id, version_id)
        return json.dumps(response)

    @app.route('/service/<string:service_id>/version', methods=['GET'])
    def list_versions(self, request, service_id):
        """
        Returns List of Service versions.
        """
        response = self.fastly_response.list_versions(request, service_id)
        return json.dumps(response)

    @app.route('/service/<string:service_id>/version/<string:version_number>/'
               'activate', methods=['PUT'])
    def activate_version(self, request, service_id, version_number):
        """
        Returns Activate Service versions.
        """
        response = self.fastly_response.activate_version(request,
                                                         service_id,
                                                         version_number)
        return json.dumps(response)

    @app.route('/service/<string:service_id>/version/<string:version_number>/'
               'deactivate', methods=['PUT'])
    def deactivate_version(self, request, service_id, version_number):
        """
        Returns Activate Service versions.
        """
        response = self.fastly_response.deactivate_version(request,
                                                           service_id,
                                                           version_number)
        return json.dumps(response)

    @app.route('/service/<string:service_id>', methods=['DELETE'])
    def delete_service(self, request, service_id):
        """
        Returns DELETE Service.
        """
        response = self.fastly_response.delete_service(request, service_id)
        return json.dumps(response)

    @app.route('/service/<string:service_id>/details', methods=['GET'])
    def get_service_details(self, request, service_id):
        """
        Returns Service details.
        """
        response = self.fastly_response.get_service_details(request,
                                                            service_id)
        return json.dumps(response)
