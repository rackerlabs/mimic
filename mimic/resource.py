"""
Resources for Mimic's core application.
"""

from __future__ import unicode_literals

import json

from io import BytesIO

from twisted.web.resource import NoResource
from twisted.web.server import Request, Site
from twisted.logger import Logger

from mimic.canned_responses.mimic_presets import get_presets
from mimic.model.behaviors import BehaviorRegistryCollection
from mimic.rest.mimicapp import MimicApp
from mimic.rest.auth_api import (
    AuthApi,
    AuthControlApiBehaviors,
    base_uri_from_request
)
from mimic.rest.noit_api import NoitApi
from mimic.rest import (fastly_api, mailgun_api, customer_api,
                        ironic_api, glance_api, valkyrie_api)
from mimic.util.helper import json_from_request
from mimic.util.helper import seconds_to_timestamp

log = Logger("mimic").info


class MimicRoot(object):
    """
    Klein routes for the root of the mimic URI hierarchy.
    """

    app = MimicApp()

    def __init__(self, core, clock=None):
        """
        :param mimic.core.MimicCore core: The core object to dispatch routes
            from.
        :param twisted.internet.task.Clock clock: The clock to advance from the
            ``/mimic/v1.1/tick`` API.
        """
        self.core = core
        self.clock = clock
        self.identity_behavior_registry = BehaviorRegistryCollection()

    @app.route("/", methods=["GET"])
    def help(self, request):
        """
        A helpful greeting message.
        """
        request.responseHeaders.setRawHeaders(b"content-type", [b"text/plain"])
        return ("To get started with Mimic, POST an authentication request to:"
                "\n\n/identity/v2.0/tokens\n").encode('utf-8')

    @app.route("/identity", branch=True)
    def get_auth_api(self, request):
        """
        Get the identity ...
        """
        return AuthApi(self.core,
                       self.identity_behavior_registry).app.resource()

    @app.route("/noit", branch=True)
    def get_noit_api(self, request):
        """
        Mock Noit api here ... until mimic allows services outside of the
        service catalog.
        """
        return NoitApi(self.core, self.clock).app.resource()

    @app.route("/sendgrid/mail.send.json", methods=['POST'])
    def send_grid_api(self, request):
        """
        Mock SendGrid api responds with a 200.
        """
        request.setResponseCode(200)
        return b''

    @app.route("/cloudmonitoring.rackspace.com", branch=True)
    def mailgun_api(self, request):
        """
        Mock Mail Gun API.
        """
        return mailgun_api.MailGunApi(self.core).app.resource()

    @app.route("/fastly", branch=True)
    def get_fastly_api(self, request):
        """
        Get the Fastly API ...
        """
        return fastly_api.FastlyApi(self.core).app.resource()

    @app.route("/v1/customer_accounts/CLOUD", branch=True)
    def get_customer_api(self, request):
        """
        Adds support for the Customer API
        """
        return customer_api.CustomerApi(self.core).app.resource()

    @app.route("/ironic/v1", branch=True)
    def ironic_api(self, request):
        """
        Mock Ironic API.
        """
        return ironic_api.IronicApi(self.core).app.resource()

    @app.route("/valkyrie/v2.0", branch=True)
    def valkyrie_api(self, request):
        """
        Mock Valkyrie API.
        """
        return valkyrie_api.ValkyrieApi(self.core).app.resource()

    @app.route('/mimic/v1.0/presets', methods=['GET'])
    def get_mimic_presets(self, request):
        """
        Return the preset values for mimic
        """
        request.setResponseCode(200)
        return json.dumps(get_presets)

    @app.route("/mimic/v1.1/tick", methods=['POST'])
    def advance_time(self, request):
        """
        Advance time by the given number of seconds.
        """
        body = json_from_request(request)
        amount = body['amount']
        self.clock.advance(amount)
        request.setResponseCode(200)
        return json.dumps({
            "advanced": amount,
            "now": seconds_to_timestamp(self.clock.seconds())
        })

    @app.route("/mimic/v1.1/IdentityControlAPI/behaviors", branch=True)
    def handle_identity_behaviors(self, request):
        """
        Handle creating/deleting behaviors for mimic identity.
        """
        api = AuthControlApiBehaviors(self.identity_behavior_registry)
        return api.app.resource()

    @app.route("/mimicking/<string:service_id>/<string:region_name>",
               branch=True)
    def get_service_resource(self, request, service_id, region_name):
        """
        Based on the URL prefix of a region and a service, where the region is
        an identifier (like ORD, DFW, etc) and service is a
        dynamically-generated UUID for a particular plugin, retrieve the
        resource associated with that service.
        """
        service_object = self.core.service_with_region(
            region_name, service_id, base_uri_from_request(request))

        if service_object is None:
            # workaround for https://github.com/twisted/klein/issues/56
            return NoResource()
        return service_object

    @app.route("/glance", branch=True)
    def glance_admin_api(self, request):
        """
        Mock for the glance admin api
        """
        return glance_api.GlanceAdminApi(self.core).app.resource()


class MimicRequest(Request, object):
    """
    Mimic requests by default are of content type application/json.
    """
    defaultContentType = b"application/json"


class MimicLoggingRequest(MimicRequest, object):
    """
    Mimic request that by default logs all incoming requests and outgoing
    responses.
    """

    def __init__(self, *args, **kwargs):
        """
        Same as the superclass's :obj:`__init__` except it also creates a
        buffer to store the response for logging.
        """
        super(MimicLoggingRequest, self).__init__(*args, **kwargs)
        self.response_body_for_logging = BytesIO()

    def process(self):
        """
        Log the incoming response before calling the superclass's
        :obj:`process`.
        """
        content = self.content.read()
        self.content.seek(0)
        log("Received request: {method} {url}\n"
            "Headers: {headers}\n"
            "{body}",
            method=self.method.decode("utf-8"), url=self.uri.decode("utf-8"),
            headers=json.dumps(
                dict((k.decode("utf-8"), [vv.decode("utf-8") for vv in v])
                     for (k, v) in self.requestHeaders.getAllRawHeaders())
            ),
            body=("\n" + content.decode("utf-8") + "\n" if content else ""))
        return super(MimicLoggingRequest, self).process()

    def write(self, data):
        """
        Collect the response data before calling the superclass's :obj:`write`.
        """
        self.response_body_for_logging.write(data)
        return super(MimicLoggingRequest, self).write(data)

    def finish(self):
        """
        Before finishing the request, log the response.
        """
        content = self.response_body_for_logging.getvalue()
        log("Responding with {code} for: {method} {url}\n"
            "Headers: {headers}\n"
            "{body}",
            method=self.method.decode("utf-8"), url=self.uri.decode("utf-8"),
            code=self.code,
            headers=json.dumps(
                dict((k.decode("utf-8"), [vv.decode("utf-8") for vv in v])
                     for (k, v) in self.responseHeaders.getAllRawHeaders())),
            body=("\n" + content.decode("utf-8") + "\n" if content else ""))
        return super(MimicLoggingRequest, self).finish()


def get_site(resource, logging=False):
    """
    :param resource: A :class:`twisted.web.resource.Resource` object.
    :return: a :class:`Site` that can be run
    """
    site = Site(resource)
    site.displayTracebacks = False
    site.requestFactory = MimicLoggingRequest if logging else MimicRequest
    return site
