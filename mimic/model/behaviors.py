"""
General-purpose utilities for customizing response behavior.
"""

import re
from characteristic import attributes, Attribute


@attributes(['name', 'predicate'])
class Criterion(object):
    """
    A criterion evaluates a predicate (callable object returning boolean)
    against an attribute with the given name.
    """

    def evaluate(self, attributes):
        """
        Extract the attribute with this Criterion's name from ``attributes``
        and evaluate it against this Criterion's predicate, returning True if
        it matches and False otherwise.
        """
        return self.predicate(attributes[self.name])


@attributes(['criteria'])
class CriteriaCollection(object):
    """
    A CriteriaCollection is a collection of Criterion which implements the same
    interface (``evaluate(attributes)``) by evaluating each of the Criterion
    objects it comprises and returning True if they all match.
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
    Return a predicate for use with a Criterion which matches a given regular
    expression.
    """
    return re.compile(value).match


@attributes([Attribute("_behaviors", default_factory=dict),
             Attribute("_criteria", default_factory=dict)])
class EventDescription(object):
    """
    A collection of behaviors which might be responses for a given event, and
    criteria which might evaluate when those behaviors are appropriate.

    :ivar default_behavior: The behavior to return from
        :obj:`BehaviorRegistry.behavior_for_attributes` if no registered
        criteria match.
    """

    def declare_behavior_creator(self, name):
        """
        Decorator which declares that the decorated function is a factory,
        taking parameters (a JSON-serialized object), and returning a behavior.

        Use like so::

            @event.declare_behavior_creator("do-something")
            def do_something_behavior(parameters):
                def do_something(args, to, behavior):
                    do_a_thing(parameters.get("thing_to_do"))
                    return result_expected_from_behavior
                return do_something
        """
        def decorator(thunk):
            thunk.behavior_name = name
            self._behaviors[name] = thunk
            return thunk
        return decorator

    def declare_default_behavior(self, default_behavior):
        """
        Decorator which declares that the decorated function is the default
        behavior that this event should provoke if no other registered behavior
        is found.

        Use like so::

            @event.decoare_default_behavior
            def do_something(args, to, behavior):
                return result_expected_from_behavior

        """
        self.default_behavior = default_behavior
        return default_behavior

    def declare_criterion(self, name):
        """
        Decorator which declares the decorated function is a criterion which
        can evaluate behavior for this event.
        """
        def decorator(thunk):
            thunk.criterion_name = name
            self._criteria[name] = thunk
            return thunk
        return decorator

    def create_behavior(self, name, parameters):
        """
        Create behavior identified by the given name, with the given
        parameters.  This is used during the process of registering a behavior.

        :param parameters: An object (deserialized from JSON) which serves as
            parameters to the named behavior creator.
        """
        return self._behaviors[name](parameters)

    def create_criteria(self, request_criteria):
        """
        Create a :obj:`CriteriaCollection` from the ``"criteria"`` section of
        an API request.
        """
        def create_criteria():
            for crit_spec in request_criteria:
                for k, v in crit_spec.items():
                    yield self._criteria[k](v)
        return CriteriaCollection(criteria=list(create_criteria()))


@attributes(["event",
             Attribute("registered_behaviors", default_factory=list)])
class BehaviorRegistry(object):
    """
    A registry of behavior.

    :ivar EventDescription event: The set of criteria and behaviors that this
        registry is operating for.
    """

    def register_from_json(self, json_payload):
        """
        Register a behavior with the given JSON payload from a request.
        """
        self.registered_behaviors.append(
            (self.event.create_behavior(json_payload["name"],
                                        json_payload["parameters"]),
             self.event.create_criteria(json_payload["criteria"])))

    def behavior_for_attributes(self, attributes):
        """
        Retrive a previously-registered behavior given the set of attributes.
        """
        for behavior, criteria in self.registered_behaviors:
            if criteria.evaluate(attributes):
                return behavior
        return self.event.default_behavior
