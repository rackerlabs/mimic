from __future__ import absolute_import, division, unicode_literals

import json

from twisted.trial.unittest import SynchronousTestCase
from mimic.rest.yo_api import YoAPI

from mimic.test.fixtures import APIDomainMockHelper
from mimic.test.helpers import json_request


class YoAPITests(SynchronousTestCase):
    """
    Tests for Yo API
    """

    def setUp(self):
        """
        Create a :obj:`APIDomainMockHelper` with :obj:`YoApi` as the only plugin
        """
        helper = APIDomainMockHelper(self, [YoAPI()])
        self.root = helper.root
        self.uri = helper.uri

    def test_send_yo(self):
        """
        The Yo API can send a Yo.
        """
        (resp, data) = self.successResultOf(json_request(
            self, self.root, b"POST", '{0}/yo/'.format(self.uri),
            json.dumps({'username': 'TESTUSER1',
                        'api_key': 'A1234567890'}).encode("utf-8")))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['success'], True)

    def test_send_yo_to_same_username_gets_same_userid(self):
        """
        Sending a Yo to the same username twice causes the same user ID
        to come back in the response.
        """
        (resp, data1) = self.successResultOf(json_request(
            self, self.root, b"POST", '{0}/yo/'.format(self.uri),
            json.dumps({'username': 'TESTUSER2',
                        'api_key': 'A1234567890'}).encode("utf-8")))
        self.assertEquals(resp.code, 200)
        (resp, data2) = self.successResultOf(json_request(
            self, self.root, b"POST", '{0}/yo/'.format(self.uri),
            json.dumps({'username': 'TESTUSER2',
                        'api_key': 'A1234567890'}).encode("utf-8")))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data1['recipient']['user_id'], data2['recipient']['user_id'])

    def test_send_yo_missing_api_key_errors(self):
        """
        Yo API sends an auth error if the request is missing an API key.
        """
        (resp, data) = self.successResultOf(json_request(
            self, self.root, b"POST", '{0}/yo/'.format(self.uri),
            json.dumps({'username': 'TESTUSER1'}).encode("utf-8")))
        self.assertEquals(resp.code, 401)
        self.assertEquals(data['error'], 'User does not have permissions for this request')

    def test_send_yo_missing_username_errors(self):
        """
        Yo API sends a bad request error if the recipient is missing.
        """
        (resp, data) = self.successResultOf(json_request(
            self, self.root, b"POST", '{0}/yo/'.format(self.uri),
            json.dumps({'api_key': 'A1234567890'}).encode("utf-8")))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data['error'], 'Can\'t send Yo without a recipient.')

    def test_send_yo_with_link_and_location_errors(self):
        """
        Yo API sends a bad request error if specifying a link and location.
        """
        (resp, data) = self.successResultOf(json_request(
            self, self.root, b"POST", '{0}/yo/'.format(self.uri),
            json.dumps({'username': 'TESTUSER3',
                        'api_key': 'A1234567890',
                        'link': 'https://example.com/test',
                        'location': '12 3rd St'}).encode("utf-8")))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data['error'], 'Can\'t send Yo with location and link.')

    def test_check_username_missing_username_errors(self):
        """
        Trying to check the username without specifying a username causes an error.
        """
        (resp, data) = self.successResultOf(json_request(
            self, self.root, b"GET", '{0}/check_username/'.format(self.uri)))
        self.assertEquals(resp.code, 400)
        self.assertEquals(data['error'], 'Must supply username')

    def test_check_existing_username_is_true(self):
        """
        Checking a username that exists gets a true response.
        """
        (resp, _) = self.successResultOf(json_request(
            self, self.root, b"POST", '{0}/yo/'.format(self.uri),
            json.dumps({'username': 'TESTUSER4',
                        'api_key': 'A1234567890'}).encode("utf-8")))
        self.assertEquals(resp.code, 200)
        (resp, data) = self.successResultOf(json_request(
            self, self.root, b"GET", '{0}/check_username/?username=TESTUSER4'.format(self.uri)))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['exists'], True)

    def test_check_non_existing_username_is_false(self):
        """
        Checking a username that do not exist gives a false response.
        """
        (resp, data) = self.successResultOf(json_request(
            self, self.root, b"GET", '{0}/check_username/?username=TESTUSER5'.format(self.uri)))
        self.assertEquals(resp.code, 200)
        self.assertEquals(data['exists'], False)
