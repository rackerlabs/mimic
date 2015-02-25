"""
Custom behaviors for the nova mimic.
"""

import re
from json import dumps

from mimic.model.behaviors import (
    EventDescription, Criterion, regexp_predicate
)
from mimic.util.helper import invalid_resource


server_creation = EventDescription()


@server_creation.behavior_creator("fail")
def create_fail_behavior(parameters):
    """
    Create a failing behavior for server creation.
    """
    status_code = parameters.get("code", 500)
    failure_message = parameters.get("message", "Server creation failed.")

    def fail_without_creating(collection, http, json, absolutize_url):
        # behavior for failing to even start to build
        http.setResponseCode(status_code)
        return dumps(invalid_resource(failure_message, status_code))
    return fail_without_creating


@server_creation.criterion("server_name")
def server_name_criterion(value):
    """
    Return a Criterion which matches the given regular expression string
    against the ``"server_name"`` attribute.
    """
    return Criterion(name='server_name', predicate=regexp_predicate(value))


@server_creation.criterion("metadata")
def metadata_criterion(value):
    """
    Return a Criterion which matches against metadata.

    :param value: ??? (FIXME this is the wrong shape)
    """
    def predicate(attribute):
        for k, v in value.items():
            if not re.compile(v).match(attribute.get(k, "")):
                return False
        return True
    return Criterion(name='metadata', predicate=predicate)
