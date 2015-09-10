# -*- test-case-name: mimic.test.test_auth -*-
"""
Defines get current customer
"""

import json

from mimic.rest.mimicapp import MimicApp
from mimic.canned_responses import fastly


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

    @app.route('/', methods=['GET'])
    def get_health(self, request):
        """
        Returns response with 200 OK.
        """
        response = self.fastly_response.get_health()
        return json.dumps(response)

    @app.route('/current_customer', methods=['GET'])
    def get_current_customer(self, request):
        """
        Returns response with current customer details.

        https://docs.fastly.com/api/account#customer_1
        """
        response = self.fastly_response.get_current_customer()
        return json.dumps(response)

    @app.route('/service', methods=['POST'])
    def create_service(self, request):
        """
        Returns POST Service.

        https://docs.fastly.com/api/config#service_5
        """
        url_data = request.args.items()
        response = self.fastly_response.create_service(url_data)
        return json.dumps(response)

    @app.route('/service/<string:service_id>/version', methods=['POST'])
    def create_version(self, request, service_id):
        """
        Returns POST Service.

        https://docs.fastly.com/api/config#version_2
        """
        response = self.fastly_response.create_version(service_id)
        return json.dumps(response)

    @app.route('/service/search', methods=['GET'])
    def get_service_by_name(self, request):
        """
        Returns response with current customer details.

        https://docs.fastly.com/api/config#service_3
        """
        url_data = request.args.items()
        data = dict((key, value) for key, value in url_data)
        service_name = data['name'][0]

        response = self.fastly_response.get_service_by_name(service_name)
        return json.dumps(response)

    @app.route(
        '/service/<string:service_id>/version/<string:version_id>/domain',
        methods=['POST'])
    def create_domain(self, request, service_id, version_id):
        """
        Returns Create Domain Response.

        https://docs.fastly.com/api/config#domain_4
        """
        url_data = request.args.items()
        response = self.fastly_response.create_domain(url_data,
                                                      service_id, version_id)
        return json.dumps(response)

    @app.route(
        '/service/<string:service_id>/version/<string:version_id>/domain/'
        'check_all',
        methods=['GET'])
    def check_domains(self, request, service_id, version_id):
        """
        Returns Check Domain.

        https://docs.fastly.com/api/config#domain_3
        """
        response = self.fastly_response.check_domains(service_id, version_id)
        return json.dumps(response)

    @app.route(
        '/service/<string:service_id>/version/<string:version_id>/backend',
        methods=['POST'])
    def create_backend(self, request, service_id, version_id):
        """
        Returns Create Backend Response.

        https://docs.fastly.com/api/config#backend_2
        """
        url_data = request.args.items()
        response = self.fastly_response.create_backend(url_data,
                                                       service_id, version_id)
        return json.dumps(response)

    @app.route(
        '/service/<string:service_id>/version/<string:version_id>/condition',
        methods=['POST'])
    def create_condition(self, request, service_id, version_id):
        """
        Returns Create Condition Response.

        https://docs.fastly.com/api/config#condition_3
        """
        url_data = request.args.items()
        response = self.fastly_response.create_condition(url_data,
                                                         service_id, version_id)
        return json.dumps(response)

    @app.route(
        '/service/<string:service_id>/version/<string:version_id>/cache_settings',
        methods=['POST'])
    def create_cache_settings(self, request, service_id, version_id):
        """
        Returns Create Cache Settings Response.

        https://docs.fastly.com/api/config#cache_settings_3
        """
        url_data = request.args.items()
        response = self.fastly_response.create_cache_settings(url_data,
                                                              service_id, version_id)
        return json.dumps(response)

    @app.route(
        '/service/<string:service_id>/version/<string:version_id>/response_object',
        methods=['POST'])
    def create_response_object(self, request, service_id, version_id):
        """
        Returns Create Cache Settings Response.

        https://docs.fastly.com/api/config#response_object_3
        """
        url_data = request.args.items()
        response = self.fastly_response.create_response_object(url_data,
                                                               service_id, version_id)
        return json.dumps(response)

    @app.route(
        '/service/<string:service_id>/version/<string:version_id>/settings',
        methods=['PUT'])
    def create_settings(self, request, service_id, version_id):
        """
        Returns Settings Response.

        https://docs.fastly.com/api/config#settings_2
        """
        url_data = request.args.items()
        response = self.fastly_response.create_settings(url_data,
                                                        service_id, version_id)
        return json.dumps(response)

    @app.route('/service/<string:service_id>/version', methods=['GET'])
    def list_versions(self, request, service_id):
        """
        Returns List of Service versions.

        https://docs.fastly.com/api/config#version_3
        """
        response = self.fastly_response.list_versions(service_id)
        return json.dumps(response)

    @app.route('/service/<string:service_id>/version/<string:version_number>/'
               'activate', methods=['PUT'])
    def activate_version(self, request, service_id, version_number):
        """
        Returns Activate Service versions.

        https://docs.fastly.com/api/config#version_5
        """
        response = self.fastly_response.activate_version(service_id,
                                                         version_number)
        return json.dumps(response)

    @app.route('/service/<string:service_id>/version/<string:version_number>/'
               'deactivate', methods=['PUT'])
    def deactivate_version(self, request, service_id, version_number):
        """
        Returns Activate Service versions.

        https://docs.fastly.com/api/config#version_6
        """
        response = self.fastly_response.deactivate_version(service_id,
                                                           version_number)
        return json.dumps(response)

    @app.route('/service/<string:service_id>', methods=['DELETE'])
    def delete_service(self, request, service_id):
        """
        Returns DELETE Service.

        https://docs.fastly.com/api/config#service_6
        """
        response = self.fastly_response.delete_service(service_id)
        return json.dumps(response)

    @app.route('/service/<string:service_id>/details', methods=['GET'])
    def get_service_details(self, request, service_id):
        """
        Returns Service details.

        https://docs.fastly.com/api/config#service_2
        """
        response = self.fastly_response.get_service_details(service_id)
        return json.dumps(response)
