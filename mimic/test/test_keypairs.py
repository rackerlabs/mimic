"""
Tests for :mod:`nova_api` and :mod:`nova_objects`.
"""
import json
from urllib import urlencode
from urlparse import parse_qs

from testtools.matchers import (
    ContainsDict, Equals, MatchesDict, MatchesListwise, StartsWith)

import treq

from twisted.trial.unittest import SynchronousTestCase

from mimic.test.helpers import json_request, request, request_with_content, validate_link_json
from mimic.rest.nova_api import NovaApi, NovaControlApi
from mimic.test.behavior_tests import (
    behavior_tests_helper_class,
    register_behavior)
from mimic.test.fixtures import APIMockHelper, TenantAuthentication
from mimic.util.helper import seconds_to_timestamp

# def create_server(helper, name=None, imageRef=None, flavorRef=None,
#                   metadata=None, diskConfig=None, body_override=None,
#                   region="ORD", request_func=json_request):
#     """
#     Create a server with the given body and returns the response object and
#     body.
#
#     :param name: Name of the server - defaults to "test_server"
#     :param imageRef: Image of the server - defaults to "test-image"
#     :param flavorRef: Flavor size of the server - defaults to "test-flavor"
#     :param metadata: Metadata of the server - optional
#     :param diskConfig: the "OS-DCF:diskConfig" setting for the server -
#         optional
#
#     :param str body_override: String containing the server args to
#         override the default server body JSON.
#     :param str region: The region in which to create the server
#     :param callable request_func: What function to use to make the request -
#         defaults to json_request (alternately could be request_with_content)
#
#     :return: either the response object, or the response object and JSON
#         body if ``json`` is `True`.
#     """
#     body = body_override
#     if body is None:
#         data = {
#             "name": name if name is not None else 'test_server',
#             "imageRef": imageRef if imageRef is not None else "test-image",
#             "flavorRef": flavorRef if flavorRef is not None else "test-flavor"
#         }
#         if metadata is not None:
#             data['metadata'] = metadata
#         if diskConfig is not None:
#             data["OS-DCF:diskConfig"] = diskConfig
#         body = json.dumps({"server": data})
#
#     create_server = request_func(
#         helper.test_case,
#         helper.root,
#         "POST",
#         '{0}/servers'.format(helper.get_service_endpoint(
#             "cloudServersOpenStack", region)),
#         body
#     )
#     return helper.test_case.successResultOf(create_server)
#
