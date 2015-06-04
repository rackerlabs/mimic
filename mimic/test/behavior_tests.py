"""
Automatically generate tests for behavior registration/deletion APIs.
Also contains helper functions for specific behavior testing.
"""
import json

from uuid import UUID, uuid4

from six import text_type, string_types

from twisted.trial.unittest import SynchronousTestCase

from zope.interface import Attribute, Interface

from mimic.test.helpers import json_request, request_with_content


class IBehaviorAPITestHelperFactory(Interface):
    """
    A class with a `classmethod` that accepts a test case and returns a
    helper.  This will be used to generate a behavior CRUD test suite.
    """
    __name__ = Attribute(
        "A name which will be used to generate the test suite name.")
    __module__ = Attribute(
        "The module in which the test suite should go.")

    def from_test_case(test_case):
        """
        A constructor that generates a provider of
        :class:`IBehaviorAPITestHelper`.

        :param test_case: An instance of a
            :class:`twisted.trial.unittest.SynchronousTestCase`
        :return: a :class:`IBehaviorAPITestHelper` provider
        """


class IBehaviorAPITestHelper(Interface):
    """
    Helper class that provides some setup and assertion methods that tests
    for behavior CRUD need.  An instance will be created and
    used for each CRUD test method.
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
    name_and_params = Attribute("""
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

    :param behavior_helper_factory: a class that implements
        :class:`IBehaviorAPITestHelperFactory`

    :return: an instance of
        :class:`twisted.trial.unittest.SynchronousTestCase`
        containing the above tests, and named "TestsFor<behavior_helper name>"
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

    Tester.__name__ = "TestsFor{0}".format(behavior_helper_factory.__name__)
    Tester.__module__ = behavior_helper_factory.__module__
    return Tester
