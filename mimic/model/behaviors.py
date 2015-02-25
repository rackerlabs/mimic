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
