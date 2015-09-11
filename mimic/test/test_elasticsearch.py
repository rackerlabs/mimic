import mock
from mock import create_autospec

from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase
from twisted.web import http

from mimic.core import MimicCore
from mimic.file_based_responses import elasticsearch
from mimic.resource import MimicRoot
from mimic.rest import elasticsearch_api
from mimic.test.helpers import json_request


class ElasticSearchAPITests(SynchronousTestCase):

    """
    Tests for the ElasticSearch API
    """

    # JSON data to be used by mocked JSON load function
    unittest_json = [
                      {
                        "order_key": 0,
                        "index": "don't_care_index",
                        "type": "don't_care_type",
                        "response": "{\"all_indexes_all_types_response\"}"
                      },
                      {
                        "order_key": 1,
                        "index": "don't_care_index",
                        "type": "test_type",
                        "response": "{\"all_indexes_test_type_response\"}"
                      },
                      {
                        "order_key": 2,
                        "index": "test_index",
                        "type": "don't_care_type",
                        "response": "{\"test_index_all_types_response\"}"
                      },
                      {
                        "order_key": 3,
                        "index": "test_index",
                        "type": "test_type",
                        "response": "{\"test_index_test_type_response\"}"
                      }
                    ]

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`ElasticSearchApi` as the only
        plugin, and create a service
        """
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = '/elasticsearch'
        self.es_api = elasticsearch_api.ElasticSearchApi(self.core)
        self.es_response = elasticsearch.ElasticSearchResponse()

    def test_get_health(self):
        """
        Verifies that ElasticSearch API is alive
        """
        (response, url_response_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/'))
        response_json = self.es_response.health()

        self.assertEqual(200, response.code)
        self.assertEqual(url_response_json, response_json)
        #self.assertTrue(False, 'forced failure of test_get_health')

    def test_get_version(self):
        """
        Returns version information for ElasticSearch API
        """
        (response, url_response_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/version'))
        response_json = self.es_response.version()

        self.assertEqual(200, response.code)
        self.assertEqual(url_response_json, response_json)

    @mock.patch('mimic.file_based_responses.elasticsearch.json')
    def test_get_index_search(self, mock_json):
        """
        Verifies that searches on specific indexes and all types works as
        expected
        """
        mock_json.load = create_autospec(elasticsearch.json.load,
                                         return_value=self.unittest_json)

        (response, url_response_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/test_index/_search'))
        response_code, response_json = \
            self.es_response.search(['test_index'], ['ALL'], {}, {})

        self.assertEqual(200, response.code)
        self.assertEqual(response_code, response.code)
        self.assertEqual(url_response_json, response_json)
        self.assertEqual(str(response_json),
                         '{"test_index_all_types_response"}')

        (response, url_response_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/invalid_index/_search'))
        response_code, response_json = \
            self.es_response.search(['invalid_index'], ['ALL'], {}, {})

        self.assertEqual(400, response.code)
        self.assertEqual(response_code, response.code)
        self.assertEqual(response_json,
                         {'message': ('response for index/type not available in'
                          ' ElasticSearch data file [elasticsearch.json]')})

    @mock.patch('mimic.file_based_responses.elasticsearch.json')
    def test_get_index_type_search(self, mock_json):
        """
        Verifies that searches on specific indexes and specific types works as
        expected
        """
        mock_json.load = create_autospec(elasticsearch.json.load,
                                         return_value=self.unittest_json)

        (response, url_response_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/test_index/test_type/_search'))
        response_code, response_json = \
            self.es_response.search(['test_index'], ['test_type'], {}, {})

        self.assertEqual(200, response.code)
        self.assertEqual(response_code, response.code)
        self.assertEqual(url_response_json, response_json)
        self.assertEqual(str(response_json),
                         '{"test_index_test_type_response"}')

        (response, url_response_json) = self.successResultOf(json_request(
            self, self.root, "GET",
            self.uri + '/invalid_index/invalid_type/_search'))
        response_code, response_json = \
            self.es_response.search(['invalid_index'], ['invalid_type'], {}, {})

        self.assertEqual(400, response.code)
        self.assertEqual(response_code, response.code)
        self.assertEqual(response_json,
                         {'message': ('response for index/type not available in'
                          ' ElasticSearch data file [elasticsearch.json]')})

    @mock.patch('mimic.file_based_responses.elasticsearch.json')
    def test_get_type_search(self, mock_json):
        """
        Verifies that searches on all indexes and specific types works as
        expected
        """
        mock_json.load = create_autospec(elasticsearch.json.load,
                                         return_value=self.unittest_json)

        (response, url_response_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/_all/test_type/_search'))
        response_code, response_json = \
            self.es_response.search(['ALL'], ['test_type'], {}, {})

        self.assertEqual(200, response.code)
        self.assertEqual(response_code, response.code)
        self.assertEqual(url_response_json, response_json)
        self.assertEqual(str(response_json),
                         '{"all_indexes_test_type_response"}')

        (response, url_response_json) = self.successResultOf(json_request(
            self, self.root, "GET",
            self.uri + '/_all/invalid_type/_search'))
        response_code, response_json = \
            self.es_response.search(['ALL'], ['invalid_type'], {}, {})

        self.assertEqual(400, response.code)
        self.assertEqual(response_code, response.code)
        self.assertEqual(response_json,
                         {'message': ('response for index/type not available in'
                          ' ElasticSearch data file [elasticsearch.json]')})

    @mock.patch('mimic.file_based_responses.elasticsearch.json')
    def test_get_search(self, mock_json):
        """
        Verifies that searches on all indexes and all types works as
        expected
        """
        mock_json.load = create_autospec(elasticsearch.json.load,
                                         return_value=self.unittest_json)

        (response, url_response_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/_search'))
        response_code, response_json = \
            self.es_response.search(['ALL'], ['ALL'], {}, {})

        self.assertEqual(200, response.code)
        self.assertEqual(response_code, response.code)
        self.assertEqual(url_response_json, response_json)
        self.assertEqual(str(response_json),
                         '{"all_indexes_all_types_response"}')

    @mock.patch('mimic.file_based_responses.elasticsearch.json')
    def test_do_search(self, mock_json):
        """
        Verifies error behaviors
        """
        mock_json.load = create_autospec(elasticsearch.json.load,
                                         return_value=self.unittest_json)

        request = http.Request(0, True)
        request.args = {"invalid_arg_key": "invalid_arg_value"}
        response_json = self.es_api.do_search([], [], request)

        self.assertEqual(400, request.code)
        self.assertEqual(response_json,
                         {'message': 'invalid request parameter'})

        mock_json.load.side_effect = TypeError()
        request = http.Request(0, True)
        response_json = self.es_api.do_search([], [], request)

        self.assertEqual(500, request.code)

    def test_verify_request_args(self):
        """
        Verifies that request arguments are verified correctly
        """
        request_args = ['bad_arg']
        valid_args = self.es_api.verify_request_args(request_args)
        self.assertFalse(valid_args)

        request_args = self.es_api.valid_request_args
        valid_args = self.es_api.verify_request_args(request_args)
        self.assertTrue(valid_args)
