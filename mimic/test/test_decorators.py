"""
Test Decorators
"""
from __future__ import absolute_import, division, unicode_literals

import json

import ddt
from twisted.trial.unittest import SynchronousTestCase

from mimic.rest.decorators import require_auth_token


class RequestMock(object):
    """
    Mock extremely simple request object for decorator testing
    """

    def __init__(self, key_value=None):
        """
        :param key_value: value to be returned by getHeader
        """
        self.key_value = key_value
        self.response_code = None

    def getHeader(self, key):
        """
        :parameter key: ignored parameter of the key to be looked up
        :returns: key value provided to constructor
        """
        return self.key_value

    def setResponseCode(self, code):
        """
        :param code: response code set by request handler
        """
        self.response_code = code


@ddt.ddt
class RequireAuthTokenTest(SynchronousTestCase):
    """
    Decorator test for extracting the auth token from a rquest object.
    """

    @require_auth_token
    def without_keyword_parameter(self, request):
        """
        Request mock without auth_token in arg spec
        """
        return json.dumps({'msg': 'hello'})

    @require_auth_token
    def with_keyword_parameter(self, request, auth_token=None):
        """
        Request mock with auth_token in arg spec
        """
        return json.dumps({'msg': 'hello', 'token': auth_token})

    @ddt.data(
        b'Some Value',
        None
    )
    def test_without_keyword(self, auth_token_value):
        """
        Call the decorator without the token in the arg spec.
        """
        request = RequestMock(key_value=auth_token_value)

        json_content = self.without_keyword_parameter(request)
        message = json.loads(json_content)
        if auth_token_value is None:
            self.assertIn('unauthorized', message)
            self.assertIn('code', message['unauthorized'])
            self.assertEqual(message['unauthorized']['code'], 401)
        else:
            self.assertIn('msg', message)
            self.assertEqual(message['msg'], 'hello')

    @ddt.data(
        b'Some Value',
        None
    )
    def test_with_keyword(self, auth_token_value):
        """
        Call the decorator with the token in the arg spec.
        """
        request = RequestMock(key_value=auth_token_value)

        json_content = self.with_keyword_parameter(request)
        message = json.loads(json_content)
        if auth_token_value is None:
            self.assertIn('unauthorized', message)
            self.assertIn('code', message['unauthorized'])
            self.assertEqual(message['unauthorized']['code'], 401)
        else:
            self.assertIn('msg', message)
            self.assertEqual(message['msg'], 'hello')
            self.assertIn('token', message)
            self.assertEqual(message['token'], auth_token_value.decode('utf-8'))
