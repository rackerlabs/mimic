"""
Model objects for the Nova mimic.
"""

from characteristic import attributes, Attribute
from random import randrange
from json import loads, dumps
import xmltodict

from mimic.util.helper import seconds_to_timestamp
from mimic.util.helper import invalid_resource

from twisted.web.http import ACCEPTED, NOT_FOUND


@attributes(["check_id", "check_name", "check_module",
             "check_target", "check_period", "check_timeout", "check_filterset"
             ])
class NoitCheck(object):

    """
    A :obj:`NoitCheck` is a representation of all the state associated with a
    check in Noit.
    """

    static_defaults = {
        "config": {
            "code": ".*",
            "header_123key.test": "400",
            "header_message123": "test",
            "method": "GET",
            "url": "http://127.0.0.1:32321/.well-known/404",
            "redirects": 10,
            "read_limit": 4567777
        },
        "state": {
            "running": "false",
            "killed": "false",
            "configured": "true",
            "disabled": "false",
            "target_ip": "23.253.6.64",
            "last_run": {
                "@now": "1422323039.361",
                "#text": "1422323039.357"
            },
            "runtime": "0.958",
            "availability": "available",
            "state": "good",
            "status": "code=200,rt=0.957s,bytes=44779,sslerror",
            "metrics": [
                {
                    "@type": "inprogress"
                },
                {
                    "@type": "current",
                    "@timestamp": None
                }
            ]
        }
    }

    @classmethod
    def create_check_from_request(cls, creation_json,
                                  check_id):
        """
        Create a :obj:`NoitCheck` from a JSON-serializable object that is parsed
        from the body of a create check request.
        """
        noit_check_json = creation_json['check']
        self = cls(
            check_id=check_id,
            check_name=noit_check_json['name'],
            check_module=noit_check_json['module'],
            check_target=noit_check_json['target'],
            check_period=noit_check_json['period'],
            check_timeout=noit_check_json['timeout'],
            check_filterset=noit_check_json['filterset']
        )
        collection.servers.append(self)
        return self

    def parse_dict_to_xml(self, json_object):
        """

        """
        return xmltodict.unparse(json_object)

    def creation_response_json():
        """

        """
        return {
            # create response goes here
        }

    def default_create_behavior(request, json, check_id):
        """
        """
        new_check = NoitCheck.create_check_from_request(json, check_id)
        response = new_check.creation_response_json()
        request.setHeader("content-type", "application/xml")
        return parse_dict_to_xml(response)


# @attributes(["request", "check_id",
#              Attribute("checks", default_factory=list)])
class NoitChecksCollection(object):

    """
    Collection of checks in a given instance of Noit
    """

    def __init__(self, request, check_id, checks=[]):
        """
        """
        self.request = request
        self.check_id = check_id

    def check_by_id(self, check_id):
        """
        Retrieve a :obj:`NoitCheck` object by its ID.
        """
        for check in self.checks:
            if check.check_id == check_id:
                return check

    def parse_xml_to_dict(self, xml_payload):
        """

        """
        return loads(dumps(xmltodict.parse(xml_payload)))


    def request_creation(self, creation_request, check_id):
        """
        Request that a check should be created in Noit.
        """
        content = str(creation_request.content.read())
        creation_json = self.parse_xml_to_dict(content)
        behavior = default_create_behavior
        return behavior(self, creation_request, creation_json, check_id)
