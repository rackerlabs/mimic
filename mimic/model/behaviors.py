"""
General-purpose utilities for customizing response behavior.
"""
import json
import re
from itertools import cycle
from uuid import UUID, uuid4

import attr

from six import text_type

from twisted.web.http import CREATED, BAD_REQUEST, NO_CONTENT, NOT_FOUND

from mimic.rest.mimicapp import MimicApp


@attr.s
class NoSuchBehaviorError(Exception):
    """
    An exception that is raised when attempting to access or delete a
    non-existant behavior based on ID.
    """
    behavior_id = attr.ib(validator=attr.validators.instance_of(UUID))


@attr.s
class Criterion(object):
    """
    A criterion evaluates a predicate (callable object returning boolean)
    against an attribute with the given name.
    """
    name = attr.ib()
    predicate = attr.ib()

    def evaluate(self, attributes):
        """
        Extract the attribute with this Criterion's name from ``attributes``
        and evaluate it against this Criterion's predicate, returning True if
        it matches and False otherwise.
        """
        return (self.name in attributes and
                self.predicate(attributes[self.name]))


@attr.s
class CriteriaCollection(object):
    """
    A CriteriaCollection is a collection of Criterion which implements the same
    interface (``evaluate(attributes)``) by evaluating each of the Criterion
    objects it comprises and returning True if they all match.
    """
    criteria = attr.ib()

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


@attr.s(these={"_behaviors": attr.ib(), "_criteria": attr.ib()}, init=False)
class EventDescription(object):
    """
    A collection of behaviors which might be responses for a given event, and
    criteria which might evaluate when those behaviors are appropriate.

    :ivar default_behavior: The behavior to return from
        :obj:`BehaviorRegistry.behavior_for_attributes` if no registered
        criteria match.

    All :class:`EventDescription`s come with a sequence behavior (named
    "sequence") by default.  (:see: :obj:`sequence_docstring` for more
    information)
    """
    def __init__(self):
        """
        Cannot use :mod:`attr` to generate the ``__init__`` function, because
        we want to also generate a seqeuence behavior by default.
        """
        self._behaviors = {}
        self._criteria = {}
        _sequence_behavior(self)

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

            @event.declare_default_behavior
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


@attr.s
class BehaviorRegistry(object):
    """
    A registry of behavior.

    :ivar EventDescription event: The event this registry is operating for.
    :ivar registered_behaviors: The set of criteria and behaviors to use for
        this event.  Currently this is just a list of tuples of
        (behavior, criteria, and uuid).
    """
    event = attr.ib()
    registered_behaviors = attr.ib(default=attr.Factory(list))

    def register_from_json(self, json_payload):
        """
        Register a behavior with the given JSON payload from a request.
        """
        behavior_id = uuid4()
        self.registered_behaviors.append(
            (self.event.create_behavior(json_payload["name"],
                                        json_payload["parameters"]),
             self.event.create_criteria(json_payload["criteria"]),
             behavior_id))
        return behavior_id

    def behavior_for_attributes(self, attributes):
        """
        Retrive a previously-registered behavior given the set of attributes.
        """
        for behavior, criteria, _ in self.registered_behaviors:
            if criteria.evaluate(attributes):
                return behavior
        return self.event.default_behavior

    def remove_behavior_by_id(self, behavior_id):
        """
        Remove a previously-registered behavior given the behavior's ID.
        """
        for i, behaviors in enumerate(self.registered_behaviors):
            b, c, b_id = behaviors
            if b_id == behavior_id:
                del self.registered_behaviors[i]
                return
        raise NoSuchBehaviorError(behavior_id=behavior_id)


@attr.s(hash=False)
class BehaviorRegistryCollection(object):
    """
    A collection of behavior registries that can be retrieved by event
    description.
    """
    _registries = attr.ib(default=attr.Factory(list))

    def registry_by_event(self, event_description):
        """
        Get a registry by event description.  If the event description is in
        the list of supported events, and there is no registry yet, create one
        and return it.

        :param EventDescription event_description: The event we want the
            registry for

        :return: a :class:`BehaviorRegistry` corresponding to the event
            description

        :raises: :class:`ValueError` if the event is not supported
        """
        for event, registry in self._registries:
            if event == event_description:
                return registry
        registry = BehaviorRegistry(event_description)
        self._registries.append((event_description, registry))
        return registry


def make_behavior_api(event_names_and_descriptions):
    """
    Create a Klein handler class which adds API endpoints for registering and
    deleting behaviors for the given events.

    This returns class which takes a single argument, ``registry_collection``,
    which is an instance of :class:`BehaviorRegistryColelction`.
    """
    @attr.s
    class BehaviorAPI(object):
        app = MimicApp()
        registry_collection = attr.ib(
            validator=attr.validators.instance_of(BehaviorRegistryCollection))

    for name, event in event_names_and_descriptions.items():
        @BehaviorAPI.app.route('/{0}'.format(name), methods=['POST'])
        def register_behavior(kl_self, request):
            """
            Register the specified behavior to cause a future event
            operation to behave in the described way.

            The request looks like this::

                {
                    # list of criteria for which requests will behave
                    # in the described way
                    "criteria": [
                        {"criteria1": "regex_pattern.*"},
                        {"criteria2": "regex_pattern.*"},
                    ],
                    # what kind of behavior: in this case,
                    # "fail the request"
                    "name": "fail",
                    # parameters for the behavior: in this case,
                    # "return a 404 with a message".
                    "parameters": {
                        "code": 404,
                        "message": "Stuff is broken, what"
                    }
                }

            The response looks like::

                {
                    "id": "this-is-a-uuid-here"
                }
            """
            reg = kl_self.registry_collection.registry_by_event(event)
            try:
                behavior_description = json.loads(request.content.read())
                behavior_id = reg.register_from_json(behavior_description)
            except (ValueError, KeyError):
                request.setResponseCode(BAD_REQUEST)
                return b''

            request.setResponseCode(CREATED)
            return json.dumps({'id': text_type(behavior_id)})

        @BehaviorAPI.app.route(
            '/{0}/<string:behavior_id>'.format(name),
            methods=['DELETE'])
        def delete_behavior(kl_self, request, behavior_id):
            """
            Remove a registered behavior with the specified ID.

            The response is a 204 with no body if successful.

            If the behavior does not exist, the response is a 404 with no
            body.
            """
            reg = kl_self.registry_collection.registry_by_event(event)
            try:
                reg.remove_behavior_by_id(UUID(behavior_id))
            except (ValueError, NoSuchBehaviorError):
                request.setResponseCode(NOT_FOUND)
            else:
                request.setResponseCode(NO_CONTENT)
            return b''

        setattr(BehaviorAPI, 'register_{0}_behavior'.format(event),
                register_behavior)
        setattr(BehaviorAPI, 'delete_{0}_behavior'.format(event),
                delete_behavior)

    return BehaviorAPI


sequence_docstring = """
    Sometimes a sequence of behaviors occur when you try to trigger an
    event in a predictable pattern.

    Takes one parameter, ``behaviors``, which is a list of specifications
    of other behaviors, similar to those specified in the request to
    create a behavior, with the addition of a behavior with a name of
    "default" that means default success.

    Each time the criterion for this behavior is matched, the next
    behavior is executed, looping back to the beginning when the list of
    behaviors is exhausted.  In other words, this creation behavior is
    stateful.

    Note that the behavior specifications here do not need a criterion,
    since the criterion is specified for the behavior overall, and each
    behavior is unconditionally executed in sequence.

    For example, to specify an alternating sequence of success and then
    failure when the criterion for the ``sequence`` behavior is matched::

        {
            "behaviors": [
                {
                    "name": "default"
                },
                {
                    "name": "fail",
                    "parameters": {
                        "code": 500,
                        "message": "synthetic error"
                    }
                }
            ]
        }
"""


def _sequence_behavior(event):
    """
    A convenience function that should for :class:`EventDescription` that,
    given an event, produces a generic behavior-creator that provides this
    sequence behavior, which is named "sequence".

    :param event: an instance of :class:`EventDescription`
    :return: a callable behavior-creator as described above
    """
    @event.declare_behavior_creator("sequence")
    def sequence(parameters):
        behavior_specification = parameters["behaviors"]
        behavior_objects = cycle([
            (
                event.create_behavior(behavior["name"],
                                      behavior["parameters"])
                if behavior["name"] != "default"
                else event.default_behavior
            )
            for behavior in behavior_specification
        ])

        def rotating_behavior(*args, **kwargs):
            current = next(behavior_objects)
            return current(*args, **kwargs)
        return rotating_behavior

    sequence.__doc__ = sequence_docstring
    return sequence
