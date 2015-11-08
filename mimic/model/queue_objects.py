"""
Models for the Queue plugin
"""

from __future__ import absolute_import, division, unicode_literals

import attr
from six import text_type

from mimic.util.helper import random_hex_generator


@attr.s
class Queue(object):
    """
    A Queue object in Cloud Queues.
    """
    name = attr.ib(validator=attr.validators.instance_of(text_type))
    id = attr.ib(validator=attr.validators.instance_of(text_type),
                 default=attr.Factory(lambda: random_hex_generator(4)))
    _messages = attr.ib(default=attr.Factory(list))

    def brief_json(self):
        """
        A brief representation of this queue that can be serialized
        via json.dumps.
        """
        return {'href': '/v1/queues/{0}'.format(self.name),
                'name': self.name}


@attr.s
class QueueCollection(object):
    """
    Models a collection of objects in the Cloud Queues business domain
    for a single tenant in a single region.
    """
    _queues = attr.ib(default=attr.Factory(list))

    def add_queue(self, queue_name):
        """
        Adds the new named queue and returns HTTP 201.
        """
        self._queues.append(Queue(name=queue_name))
        return (None, 201)

    def list_queues(self):
        """
        Lists all queues in the collection.
        """
        return {'queues': [queue.brief_json() for queue in self._queues]}, 200

    def delete_queue(self, queue_name):
        """
        Deletes the named queue from the collection, if it exists.

        Returns HTTP 204.
        """
        self._queues[:] = [queue for queue in self._queues
                           if queue.name != queue_name]
        return None, 204
