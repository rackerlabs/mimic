# -*- test-case-name: mimic.test.test_auth -*-
"""
Implements mock for ElasticSearch API
"""

import json

from mimic.file_based_responses import elasticsearch
from mimic.rest.mimicapp import MimicApp


class ElasticSearchApi(object):

    """
    Rest endpoints for mocked ElasticSearch api.
    """

    app = MimicApp()

    indexes = []
    types = []

    # Valid parameters for ElasticSearch request
    valid_request_args = \
        ['q', 'df', 'analyzer', 'lowercase_expanded_terms', 'analyze_wildcard',
         'default_operator', 'lenient', 'explain', '_source', 'fields', 'sort',
         'track_scores', 'timeout', 'terminate_after', 'from', 'size',
         'search_type']

    def __init__(self, core):
        """
        :param MimicCore core: The core to which this ElasticSearch Api will be
            communicating.
        """
        self.core = core
        self.services = {}
        self.es_response = elasticsearch.ElasticSearchResponse()

    @app.route('/', methods=['GET'])
    def get_health(self, request):
        """
        Report if ElasticSearch API is alive
        """
        response = self.es_response.health()
        return json.dumps(response)

    @app.route('/version', methods=['GET'])
    def get_version(self, request):
        """
        Report version information for ElasticSearch API
        """
        response = self.es_response.version()
        return json.dumps(response)

    @app.route('/<string:indexes_str>/_search', methods=['GET'])
    def get_index_search(self, request, indexes_str):
        """
        Return data for specific indexes and all types
        """
        indexes = indexes_str.split(",")
        types = ['ALL']
        response = self.do_search(indexes, types, request)
        return json.dumps(response)

    @app.route('/<string:indexes_str>/<string:types_str>/_search',
               methods=['GET'])
    def get_index_type_search(self, request, indexes_str, types_str):
        """
        Return data for specific indexes and specific types
        """
        indexes = indexes_str.split(",")
        types = types_str.split(",")
        response = self.do_search(indexes, types, request)
        return json.dumps(response)

    @app.route('/_all/<string:types_str>/_search', methods=['GET'])
    def get_type_search(self, request, types_str):
        """
        Return data for all indexes and specific types
        """
        indexes = ['ALL']
        types = types_str.split(",")
        response = self.do_search(indexes, types, request)
        return json.dumps(response)

    @app.route('/_search', methods=['GET'])
    def get_search(self, request):
        """
        Return data for all indexes and all types
        """
        indexes = ['ALL']
        types = ['ALL']
        response = self.do_search(indexes, types, request)
        return json.dumps(response)

    def do_search(self, indexes, types, request):
        """
        Helper function that verifies and breaks down request before executing
        search
        """
        if request.args != None and not self.verify_request_args(request.args):
            # an argument sent with the request is not valid for ElasticSearch
            request.setResponseCode(400)
            return {'message': 'invalid request parameter'}

        if request.content == None:
            request_data = None
        else:
            request_data = request.content.read()

        resp_code, response = \
            self.es_response.search(indexes, types, request.args, request_data)

        request.setResponseCode(resp_code)
        return response

    def verify_request_args(self, args):
        """
        returns boolean indicating if all args are valid or not
        """
        all_args_valid = True
        for arg in args:
            if arg not in self.valid_request_args:
                all_args_valid =  False
        return all_args_valid
