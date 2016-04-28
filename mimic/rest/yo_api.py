"""
API domain mock for Yo.
"""

from __future__ import absolute_import, division, unicode_literals

import attr
import json

from twisted.plugin import IPlugin
from mimic.imimic import IAPIDomainMock
from mimic.rest.mimicapp import MimicApp

from zope.interface import implementer

from mimic.model.yo_objects import YoCollections
from mimic.util.helper import random_hex_generator


@implementer(IAPIDomainMock, IPlugin)
@attr.s
class YoAPI(object):
    """
    API domain mock for api.justyo.co.
    """
    _resource = attr.ib(default=attr.Factory(lambda: YoAPIRoutes().app.resource()))

    def domain(self):
        """
        The Yo API is found at api.justyo.co.
        """
        return "api.justyo.co"

    def resource(self):
        """
        The resource for the Yo API.
        """
        return self._resource


@attr.s(hash=False)
class YoAPIRoutes(object):
    """
    Klein routes for Yo API methods.
    """
    yo_collections = attr.ib(default=attr.Factory(YoCollections))

    app = MimicApp()

    @app.route("/yo/", methods=['POST'])
    def rpc_send_yo(self, request):
        """
        Sends a Yo RPC style.
        """
        body = json.loads(request.content.read().decode("utf-8"))

        if 'api_key' not in body:
            request.setResponseCode(401)
            return json.dumps({'error': 'User does not have permissions for this request',
                               'errors': [{'message': ('User does not have permissions '
                                                       'for this request')}]})

        if 'username' not in body:
            request.setResponseCode(400)
            return json.dumps({'error': 'Can\'t send Yo without a recipient.',
                               'errors': [{'message': 'Can\'t send Yo without a recipient.'}]})

        if 'link' in body and 'location' in body:
            request.setResponseCode(400)
            return json.dumps({'error': 'Can\'t send Yo with location and link.',
                               'errors': [{'message': 'Can\'t send Yo with location and link.'}]})

        user = self.yo_collections.get_or_create_user(body['username'])

        request.setResponseCode(200)
        return json.dumps({'success': True,
                           'yo_id': random_hex_generator(12),
                           'recipient': user.to_json()})

    @app.route("/check_username/", methods=['GET'])
    def check_username(self, request):
        """
        Checks to see if a user exists.
        """
        if b'username' not in request.args:
            request.setResponseCode(400)
            return json.dumps({'error': 'Must supply username',
                               'errors': [{'message': 'Must supply username'}]})

        username = request.args[b'username'][0].strip().decode("utf-8")
        request.setResponseCode(200)
        return json.dumps({'exists': username.upper() in self.yo_collections.users})
