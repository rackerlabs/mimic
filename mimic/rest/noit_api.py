# -*- test-case-name: mimic.test.test_noit -*-
"""
Defines get token, impersonation
"""
import xmltodict
from uuid import UUID
from mimic.rest.mimicapp import MimicApp
from mimic.canned_responses.noit import (create_check, get_check,
                                         get_all_checks, delete_check,
                                         test_check)


# TO DO:
# https://github.com/rackerlabs/mimic/issues/203


class NoitApi(object):

    """
    Rest endpoints for mocked Noit api.
    """

    app = MimicApp()

    def __init__(self, core, clock):
        """
        :param MimicCore core: The core to which this NoitApi will be
            communicating.
        """
        self.core = core
        self.clock = clock

    def validate_check_payload(self, request):
        """
        Validate the check request payload and returns the response code
        """
        content = str(request.content.read())
        try:
            payload = xmltodict.parse(content)
        except:
            return 500, None
        attributes = ["name", "module", "target", "period", "timeout",
                      "filterset"]
        for each in attributes:
            if not payload["check"]["attributes"].get(each):
                return 404, None
        return 200, payload["check"]["attributes"]

    @app.route('/checks/test', methods=['POST'])
    def test_check(self, request):
        """
        Validates the check xml and returns the metrics
        """
        response = self.validate_check_payload(request)
        if (response[0] == 200):
            request.setHeader("content-type", "application/xml")
            response_body = test_check(response[1]["module"])
            return xmltodict.unparse(response_body)
        request.setResponseCode(response[0])
        return

    @app.route('/checks/set/<check_id>', methods=['PUT'])
    def set_check(self, request, check_id):
        """
        Creates a check for the given check_id. If the check_id already
        exists, then it updates that check.
        TBD: Include error 400 and 500s. Module cannot be updated (test
            against noit service to see the response code expected)
        """
        try:
            UUID(check_id)
        except (ValueError, AttributeError):
            request.setResponseCode(500)
            return
        request.setHeader("content-type", "application/xml")
        response = self.validate_check_payload(request)
        request.setResponseCode(response[0])
        if (response[0] == 200):
            response_body = create_check(response[1], check_id)
            return xmltodict.unparse(response_body)
        return

    @app.route('/checks/show/<check_id>', methods=['GET'])
    def get_checks(self, request, check_id):
        """
        Return the current configuration and state of the specified check.
        """
        request.setHeader("content-type", "application/xml")
        return xmltodict.unparse(get_check(check_id))

    @app.route('/config/checks', methods=['GET'])
    def get_all_checks(self, request):
        """
        Return the current configuration and state of all checks.
        """
        request.setHeader("content-type", "application/xml")
        return xmltodict.unparse(get_all_checks())

    @app.route('/checks/delete/<check_id>', methods=['DELETE'])
    def delete_checks(self, request, check_id):
        """
        Delete the specified check and return 204 response code
        """
        response_code = delete_check(check_id) or 200
        request.setResponseCode(response_code)
        request.setHeader("content-type", "application/xml")
        return
