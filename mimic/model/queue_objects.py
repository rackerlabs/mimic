"""
Models for the Queue plugin
"""

from __future__ import absolute_import, division, unicode_literals

import attr
from six import text_type
from twisted.internet.interfaces import IReactorTime

from mimic.util.helper import random_hex_generator


@attr.s
class Message(object):
    """
    A Message object in Cloud Queues.
    """
    ttl = attr.ib(validator=attr.validators.instance_of(int))
    body = attr.ib(validator=attr.validators.instance_of(dict))
    queue_name = attr.ib(validator=attr.validators.instance_of(text_type))
    posted_by = attr.ib(validator=attr.validators.instance_of(text_type))
    posted_at = attr.ib(validator=attr.validators.instance_of(int))
    id = attr.ib(validator=attr.validators.instance_of(text_type),
                 default=attr.Factory(lambda: random_hex_generator(12)))

    def to_json(self, current_time):
        """
        A representation of this message that can be serialized via json.dumps.
        """
        return {'body': self.body,
                'age': current_time - self.posted_at,
                'href': self.href(),
                'ttl': self.ttl}

    def href(self):
        """
        Returns the URL path representing this message.
        """
        return '/v1/queues/{0}/messages/{1}'.format(self.queue_name, self.id)

    def is_expired_at(self, current_time):
        """
        Returns True if the message is expired at the given time.
        """
        return (self.posted_at + self.ttl) < current_time


@attr.s
class Queue(object):
    """
    A Queue object in Cloud Queues.
    """
    name = attr.ib(validator=attr.validators.instance_of(text_type))
    id = attr.ib(validator=attr.validators.instance_of(text_type),
                 default=attr.Factory(lambda: random_hex_generator(4)))
    _messages = attr.ib(default=attr.Factory(list))

    def _clear_expired_messages(self, current_time):
        """
        Clears expired messages from the queue.
        """
        self._messages[:] = [message for message in self._messages
                             if not message.is_expired_at(current_time)]

    def brief_json(self):
        """
        A brief representation of this queue that can be serialized
        via json.dumps.
        """
        return {'href': '/v1/queues/{0}'.format(self.name),
                'name': self.name}

    def post_messages(self, messages, client_id, current_time):
        """
        Posts a series of messages to the message queue.
        """
        self._clear_expired_messages(current_time)
        new_messages = [Message(ttl=message['ttl'],
                                body=message['body'],
                                queue_name=self.name,
                                posted_by=client_id,
                                posted_at=current_time)
                        for message in messages]
        self._messages.extend(new_messages)
        response_json = {'partial': False,
                         'resources': [message.href() for message in new_messages]}
        return response_json, 201

    def list_messages(self, client_id, current_time, echo):
        """
        Lists messages (that the client can see).

        If the echo parameter is set to true, the client sees all messages.
        Otherwise, the client only sees messages posted by other clients.
        """
        self._clear_expired_messages(current_time)
        response_json = {'messages': [message.to_json(current_time)
                                      for message in self._messages
                                      if echo or message.posted_by != client_id],
                         'links': []}
        return (response_json, 200) if response_json['messages'] else (None, 204)


@attr.s
class QueueCollection(object):
    """
    Models a collection of objects in the Cloud Queues business domain
    for a single tenant in a single region.
    """
    _clock = attr.ib(validator=attr.validators.provides(IReactorTime))
    _queues = attr.ib(default=attr.Factory(list))

    def _current_time(self):
        """
        Cloud Queues deals with time mostly in integer numbers of seconds.

        This method gives the time in seconds, truncated to an integer.
        """
        return int(self._clock.seconds())

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

    def list_messages_for_queue(self, queue_name, client_id, echo):
        """
        Lists all messages in the named queue.
        """
        for queue in self._queues:
            if queue.name == queue_name:
                return queue.list_messages(client_id, self._current_time(), echo)
        return None, 204

    def post_messages_to_queue(self, queue_name, messages, client_id):
        """
        Post a series of messages to the named queue.
        """
        for queue in self._queues:
            if queue.name == queue_name:
                return queue.post_messages(messages, client_id, self._current_time())
        return None, 404
