"""
Custom behaviors for the nova mimic.
"""

import re
from json import dumps
from characteristic import attributes, Attribute
from mimic.util.helper import invalid_resource


@attributes([Attribute("behaviors", default_factory=dict)])
class BehaviorLookup(object):

    """
    A collection of behaviors with a related schema.
    """

    def behavior_creator(self, name):
        """
        Decorator which declares the decorated function is a behavior for this
        table.
        """
        def decorator(thunk):
            thunk.behavior_name = name
            self.behaviors[name] = thunk
            return thunk
        return decorator

    def create_behavior(self, name, parameters):
        """
        Create behavior identified by the given name, with the given
        parameters.  This is used during the process of registering a behavior.

        :param parameters: An object (deserialized from JSON) which serves as
            parameters to the named behavior creator.
        """
        return self.behaviors[name](parameters)


server_creation = BehaviorLookup()


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


"""
POST /mimicking/...nova-behavior.../...your-tenant.../behaviors/creation/

{
    "criteria": [
        {"tenant_id": "maybe_fail_.*"},
        {"server_name": "failing_server_.*"},
        {"metadata": {"key_we_should_have": "fail",
                      "key_we_should_not_have": null}}
    ],
    "name": "fail",
    "parameters": {
        "code": 404,
        "message": "Stuff is broken, what"
    }
}
"""


@attributes(['name', 'predicate'])
class Criterion(object):

    """

    """

    def evaluate(self, attributes):
        """

        """
        return self.predicate(attributes[self.name])


@attributes(['criteria'])
class CriteriaCollection(object):

    """

    """

    def evaluate(self, attributes):
        """
        Evaluate the list of :obj:`Criterion`.
        """
        for criterion in self.criteria:
            if not criterion.evaluate(attributes):
                return False
        return True


def regexp_predicate(value):
    """

    """
    return re.compile(value).match


def tenant_id_criterion(value):
    """

    """
    return Criterion(name='tenant_id', predicate=regexp_predicate(value))


def server_name_criterion(value):
    """

    """
    return Criterion(name='server_name', predicate=regexp_predicate(value))


def metadata_criterion(value):
    """

    """
    name = value['name']
    value_predicate = regexp_predicate(value['value'])

    def predicate(metadata):
        return value_predicate(metadata.get(name))
    return Criterion(name='metadata', predicate=predicate)

nova_criterion_factories = {
    "tenant_id": tenant_id_criterion,
    "server_name": server_name_criterion,
    "metadata": metadata_criterion
}


def criteria_collection_from_request_criteria(request_criteria,
                                              name_to_criterion):
    """
    Create a :obj:`CriteriaCollection` from the ``"criteria"`` section of an
    API request.
    """
    def create_criteria():
        for crit_spec in request_criteria:
            for k, v in crit_spec.items():
                yield name_to_criterion[k](v)
    return CriteriaCollection(criteria=list(create_criteria()))
