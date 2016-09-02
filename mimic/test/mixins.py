"""
Mixins for various tests that repeat
"""
from mimic.test.helpers import json_request


class IdentityAuthMixin(object):
    """
    Common Auth Failure Tests
    """

    def test_auth_fail(self):
        """
        HTTP Verb with no X-Auth-Token header results in 401.
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri))

        self.assertEqual(response.code, 401)
        self.assertEqual(json_body['unauthorized']['code'], 401)


class InvalidJsonMixin(object):
    """
    Common JSON Body Failure Tests
    """

    def test_invalid_json_body(self):
        """
        HTTP Verb will generate 400 when an invalid JSON body is provided.
        """
        (response, json_body) = self.successResultOf(
            json_request(self, self.root, self.verb,
                         self.uri,
                         body=b'<xml>ensure json failure',
                         headers=self.headers))

        self.assertEqual(response.code, 400)
        self.assertEqual(json_body['badRequest']['code'], 400)
        self.assertEqual(json_body['badRequest']['message'],
                         'Invalid JSON request body')
