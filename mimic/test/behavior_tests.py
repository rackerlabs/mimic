"""
Automatically generate tests for behavior registration/deletion APIs.
(:see: :func:`behavior_tests_helper_class`).

Also contains helper functions for specific behavior testing.
(:see: :func:`register_behavior`)
"""
import json

from uuid import UUID, uuid4

from six import text_type, string_types

from twisted.trial.unittest import SynchronousTestCase

from zope.interface import Attribute, Interface, implementer
from zope.interface.verify import verifyObject

from mimic.test.helpers import json_request, request_with_content


class IBehaviorAPITestHelperFactory(Interface):
    """
    A class with a `classmethod` that accepts a test case and returns a
    helper.  This will be used to generate a behavior CRUD test suite.
    """
    name = Attribute(
        "A name which will be used to generate the test suite name.")
    module = Attribute(
        "The module in which the test suite should go.")

    def from_test_case(test_case):
        """
        A constructor that generates a provider of
        :class:`IBehaviorAPITestHelper`.  This should return a new provider
        every time.

        :see: :func:`make_behavior_tests` implementation

        :param test_case: An instance of a
            :class:`twisted.trial.unittest.SynchronousTestCase`
        :return: a :class:`IBehaviorAPITestHelper` provider
        """


class IBehaviorAPITestHelper(Interface):
    """
    Set-up and assertion methods required for testing behavior CRUD.
    """
    root = Attribute("The root resource for mimic.")
    behavior_api_endpoint = Attribute(
        "The API endpoint for behaviors for the event to be tested.")
    criteria = Attribute("""
        A list of criteria for the behaviors to be injected.  Example::

            [
                {"criteria1": "regex_pattern.*"},
                {"criteria2": "regex_pattern.*"},
            ]
        """)

    names_and_params = Attribute("""
        An list of 1 or 2 tuples of name and parameters, which together
        with the criteria, can form a behavior specification.  Any more than
        2 will ignored.  Example::

            # tuples of (name of the behavior, parameters for the behavior)
            [
                ("fail", {"code": 500, "message": "Stuff is broken"}),
                ("fail", {"code": 404, "message": "Stuff doesn't exist"})
            }
        """)

    def trigger_event():
        """
        Make a request to the regular API that this behavior event modifies.
        Note that the event should conform to the criteria given.

        :return: a tuple of (:class:`twisted.web.client.Response`, `str` or
            `dict` or `list` body).  The body can either be a string, or
            JSON blob loaded into a dictionary or array, just so long as the
            validation functions can handle it.
        """

    def validate_injected_behavior(name_and_params, response, body):
        """
        Validate that the named behavior was triggered as opposed to the
        default behavior or some other behavior.

        :param name_and_params: The name and parameters of the behavior to
            trigger - this will be one of the ones specified in
            :ivar:`name_and_params`.
        :param response: The response from triggering the event.
        :param body: The response body from triggering the event.

        :raises: :class:`FailTest` using an instance of
            :class:`twisted.trial.unittest.SynchronousTestCase` if the
            behavior was not triggered correctly.
        :return: `None` if the behavior was triggered correctly.
        """

    def validate_default_behavior(response, body):
        """
        Validate that the default behavior was triggered as opposed to
        some other behavior.

        :param response: The response from triggering the event.
        :param body: The response body from triggering the event.

        :raises: :class:`FailTest` using a
            :class:`twisted.trial.unittest.SynchronousTestCase` if the
            default behavior was not triggered correctly.
        :return: `None` if the default behavior was triggered correctly.
        """


def make_behavior_tests(behavior_helper_factory):
    """
    Generate a test suite containing test that validate that:

    - deleting a behavior will revert to the underlying
      behavior.  If 2 behaviors are provided, will also assert that the
      first behavior registered will be the behavior used, and that deleting
      it means the second mock takes over.  Deleting that will revert to
      default behavior.  If only 1 behavior is provided, it will just test
      that deleting it reverts to default behavior.

    - deleting an invalid behavior for will result in a 404.

    - providing invalid JSON will result in a 400 when creating the behavior.

    - sequence behavior will rotate through the behaviors and default behavior

    :param behavior_helper_factory: a class that implements
        :class:`IBehaviorAPITestHelperFactory`

    :return: an instance of
        :class:`twisted.trial.unittest.SynchronousTestCase`
        containing the above tests, and named
        "TestsFor<behavior_helper_factory.name>"
    """
    class Tester(SynchronousTestCase):
        """Tests for behavior API crud that uses {0}""".format(
            behavior_helper_factory.__name__)

        def setUp(self):
            self.bhelper = behavior_helper_factory.from_test_case(self)

        def delete_behavior(self, behavior_id, status=204, expected_body=b''):
            """
            Given a behavior ID, attempts to delete it.
            """
            response, body = self.successResultOf(request_with_content(
                self, self.bhelper.root, "DELETE",
                "{0}/{1}".format(self.bhelper.behavior_api_endpoint,
                                 behavior_id)))
            self.assertEqual(response.code, status)
            self.assertEqual(body, expected_body)

        def test_deleting_nonexistant_behavior_fails(self):
            """
            Deleting a non-existant behavior ID fails with a 404.  Similarly
            with an invalid behavior ID.
            """
            for invalid_id in (text_type(uuid4()), "not-even-a-uuid"):
                self.delete_behavior(invalid_id, status=404)

        def test_providing_invalid_json_fails_with_400(self):
            """
            Providing invalid JSON for the behavior registration request
            results in a 400.
            """
            name, params = self.bhelper.names_and_params[0]
            almost_correct = json.dumps({'name': name, 'parameters': params})
            for invalid in ('', '{}', almost_correct):
                response, body = self.successResultOf(request_with_content(
                    self, self.bhelper.root, "POST",
                    self.bhelper.behavior_api_endpoint,
                    invalid))
                self.assertEqual(response.code, 400)
                self.assertEqual(b"", body)

        def test_deleting_behavior_removes_top_behavior(self):
            """
            If deleting a behavior succeeds, and there were other behaviors
            the first behavior was masking, then the next behavior is used.
            When there are no more behaviors, the default behavior is used.
            """
            names_and_params = self.bhelper.names_and_params[:2]
            behavior_ids = []
            for i, n_and_p in enumerate(names_and_params):
                name, params = n_and_p
                behavior_ids.append(register_behavior(
                    self,
                    self.bhelper.root,
                    self.bhelper.behavior_api_endpoint,
                    name,
                    params,
                    self.bhelper.criteria))

            self.bhelper.validate_injected_behavior(
                names_and_params[0], *self.bhelper.trigger_event())

            self.delete_behavior(behavior_ids[0])

            if len(behavior_ids) > 1:
                self.bhelper.validate_injected_behavior(
                    names_and_params[1], *self.bhelper.trigger_event())

                self.delete_behavior(behavior_ids[1])

            self.bhelper.validate_default_behavior(
                *self.bhelper.trigger_event())

        def test_sequence_behavior(self):
            """
            There is also a behavior, sequence, which should rotate through
            all the behaviors provided.
            """
            names_and_params = self.bhelper.names_and_params[:2]
            behaviors = [{'name': name, 'parameters': params}
                         for name, params in names_and_params]

            register_behavior(
                self, self.bhelper.root,
                self.bhelper.behavior_api_endpoint,
                behavior_name="sequence",
                parameters={"behaviors": behaviors + [{'name': 'default'}]},
                criteria=self.bhelper.criteria)

            # The results rotate through the first behavior, second behavior
            # (if present), the default behavior, and then back, in order.
            for i in range(2):
                self.bhelper.validate_injected_behavior(
                    names_and_params[0], *self.bhelper.trigger_event())

                if len(names_and_params) > 1:
                    self.bhelper.validate_injected_behavior(
                        names_and_params[1], *self.bhelper.trigger_event())

                self.bhelper.validate_default_behavior(
                    *self.bhelper.trigger_event())

    Tester.__name__ = "TestsFor{0}".format(behavior_helper_factory.name)
    Tester.__module__ = behavior_helper_factory.module
    return Tester


def behavior_tests_helper_class(klass):
    """
    Generate a test suite containing test that validate that:

    - deleting a behavior will revert to the underlying
      behavior.  If 2 behaviors are provided, will also assert that the
      first behavior registered will be the behavior used, and that deleting
      it means the second mock takes over.  Deleting that will revert to
      default behavior.  If only 1 behavior is provided, it will just test
      that deleting it reverts to default behavior.

    - deleting an invalid behavior for will result in a 404.

    - providing invalid JSON will result in a 400 when creating the behavior.

    - sequence behavior will rotate through the behaviors (including the
        default behavior).

    Note that these ONLY test that you have correctly added behavior CRUD
    (and that if multiple behaviors are added for the same criteria, they
    supercede each other rather than interfere).  This also happens to test
    sequence behavior, because that is a utility that is provided by
    :mod:`mimic.model.behaviors`.

    This generated test suite is not meant to be a replacement for tests that
    ensure that custom behaviors themselves do the right thing.

    A basic version of ``klass`` should have all the methods and attributes
    required by :class:`IBehaviorAPITestHelper`, and an `__init__` function
    that takes a :class:`twisted.trial.unittest.SynchronousTestCase`.

    Example usage::

        @behavior_tests_helper_class
        class MyPluginBehaviorAPI(object):
            criteria = [{"criteria_name": "my_regex.*"}]
            names_and_parameters = [
                ("behavior_name1", {"param1": "val1"}),
                ("behavior_name2", {"param1": "val2"})
            ]

            def __init__(self, test_case):
                self.test_case = test_case
                self.helper = APIMockHelper(test_case, [])
                self.root = helper.root
                self.behavior_api_endpoint = "{0}/behaviors/mytype".format(
                    self.helper.get_service_endpoint(
                        "control_plane_service_name"))

            def trigger_event(self):
                return json_request(
                    self.test_case, self.root, "POST",
                    self.helper.get_service_endpoint("real_service_name),
                    {"json": {"with": {"criteria_name": "my_regex}}})

            def validate_injected_behavior(self, name_and_params, response,
                                           body):
                name, params = name_and_params
                if name == "behavior_name1":
                    self.test_case.assertEquals(response.code, 500)
                else:
                    self.test_case.assertEquals(response.code, 400)

            def validate_default_behavior(self, response, body):
                self.test_case.assertEquals(response.code, 201)


    This will produce trial output like the following::

        <full name python module path to class>.TestsForMyPluginBehaviorAPI
            test_deleting_behavior_removes_top_behavior ...           [OK]
            test_deleting_nonexistant_behavior_fails ...              [OK]
            test_providing_invalid_json_fails_with_400 ...            [OK]


    This decorator is syntactic sugar for
    #. declaring that ``klass`` implements :class:`IBehaviorAPITestHelper` if
       it hasn't already been declared, and verifying that it does
    #. assigning a ``name`` and ``module`` attribute to ``klass`` if they
       aren't assigned already
    #. setting ``from_test_case`` to be a method that calls the ``klass``
       initializer with a test case if ``from_test_case`` is not already
       provided
    #. declaring that ``klass`` also implements
       :class:`IBehaviorAPITestHelperFactory`
    #. calling :func:`make_behavior_tests` on ``klass``

    This decorator will also validate that ``klass`` correctly implements
    :class:`IBehaviorAPITestHelper`.  It creates an instance of ``klass`` to
    do so.

    :param klass: a class that implements :class:`IBehaviorAPITestHelper`,
        although it does not have to declare that it does (this decorator will
        do so)

    :raises: :class:`zope.interface.verify.BrokenImplementation` if ``klass`
        does not implement :class:`IBehaviorAPITestHelper`
    :return: an instance of
        :class:`twisted.trial.unittest.SynchronousTestCase`
        containing the above tests, and named "TestsFor<``klass.__name__``>".
        The test suite will run as if it were in the same module as
        ``klass``, unless the ``name`` or ``module`` attributes of ``klass``
        were already specified.
    """
    klass = implementer(IBehaviorAPITestHelper,
                        IBehaviorAPITestHelperFactory)(klass)

    if getattr(klass, 'name', None) is None:
        setattr(klass, 'name', klass.__name__)

    if getattr(klass, 'module', None) is None:
        setattr(klass, 'module', klass.__module__)

    if getattr(klass, 'from_test_case', None) is None:
        setattr(klass, 'from_test_case',
                classmethod(lambda cls, test_case: cls(test_case)))

    instance = klass.from_test_case(SynchronousTestCase())
    verifyObject(IBehaviorAPITestHelper, instance)
    verifyObject(IBehaviorAPITestHelperFactory, instance)

    return make_behavior_tests(klass)


def register_behavior(test_case, root, uri, behavior_name, parameters,
                      criteria):
    """
    Register a particular behavior.

    :param test_case: the test case with which to make assertions
    :param root: A mimic root API object
    :param str uri: The uri fo the behavior resource to register.
    :param str behavior_name: The name of the behavior
    :param dict parameters: A dictionary of parameters to pass to the behavior
    :param list criteria: The criteria for which this behavior should be
        applied.

    :return: The behavior ID of the registered behavior.
    """
    behavior_json = {"name": behavior_name,
                     "parameters": parameters,
                     "criteria": criteria}
    response, body = test_case.successResultOf(json_request(
        test_case, root, "POST", uri, json.dumps(behavior_json)))

    test_case.assertEqual(response.code, 201)
    behavior_id = body.get("id")
    test_case.assertIsInstance(behavior_id, string_types)
    test_case.assertEqual(UUID(behavior_id).version, 4)
    return behavior_id
