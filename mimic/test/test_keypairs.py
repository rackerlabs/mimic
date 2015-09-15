"""
Tests for :mod:`nova_api` and :mod:`nova_objects`.
"""
import json
from urllib import urlencode
from urlparse import parse_qs

import treq
from IPython import embed;

from twisted.trial.unittest import SynchronousTestCase

from mimic.test.helpers import json_request, request, request_with_content, validate_link_json
from mimic.rest.nova_api import NovaApi, NovaControlApi
from mimic.test.behavior_tests import (
    behavior_tests_helper_class,
    register_behavior)
from mimic.test.fixtures import APIMockHelper, TenantAuthentication
from mimic.util.helper import seconds_to_timestamp

class KeyPairTests(SynchronousTestCase):

    """
    Tests for keypairs
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`NovaApi` as the only plugin
        """
        nova_api = NovaApi(["ORD", "MIMIC"])
        self.helper = self.helper = APIMockHelper(
            self, [nova_api, NovaControlApi(nova_api=nova_api)]
        )
        self.root = self.helper.root
        self.clock = self.helper.clock
        self.uri = self.helper.uri

    def test_create_keypair(self):
        api_helper = self.helper
        kp_body = {
            "keypair": {
                "name": "test_lp",
                "public_key": "ssh-rsa testkey/"
            }
        }

        resp, body = self.successResultOf(json_request(
            self, api_helper.root, "POST", api_helper.uri + '/os-keypairs',
            kp_body
        ))