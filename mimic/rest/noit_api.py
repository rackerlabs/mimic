# -*- test-case-name: mimic.test.test_noit -*-
"""
Defines get token, impersonation
"""
import xmltodict
from twisted.web.server import Request
from mimic.rest.mimicapp import MimicApp
from mimic.canned_responses.noit import create_check, get_check, get_checks


Request.defaultContentType = 'application/xml'


class NoitApi(object):

    """
    Rest endpoints for mocked Noit api.
    """

    app = MimicApp()

    def __init__(self, core):
        """
        :param MimicCore core: The core to which this NoitApi will be
            communicating.
        """
        self.core = core

    @app.route('/checks/set/<check_id>', methods=['PUT'])
    def set_check(self, check_id, request):
        """
        Creates a check for the given check_id. If the check_id already exists, then
        it updates that check.
        TBD: Include error 400 and 500s. Module cannot be updated (test against noit service
            to see the response code expected)
        """
        # validate check_id is a uuid ?? does noit fail if not?
        content = xmltodict(request)
        attributes = ["name", "module", "target", "period", "timeout",
                      "filterset"]
        request.setResponseCode(200)
        request.setHeader("content-type", "application/xml")
        for each in attributes:
            if not content.get("each"):
                request.setResponseCode(400)
                return
        return create_check(content, check_id)

    @app.route('/check/show/<check_id>', methods=['GET'])
    def get_checks(self, request, check_id):
        """
        Return the current configuration and state of the specified check.
        """
        request.setResponseCode(200)
        request.setHeader("content-type", "application/xml")
        return get_check(check_id)

    @app.route('/checks', methods=['GET'])
    def get_all_checks(self, request):
        """
        Return the current configuration and state of the specified check.
        """
        request.setResponseCode(200)
        request.setHeader("content-type", "application/xml")
        return get_checks()
