"""
Helper objects for tests, mostly to allow testing HTTP routes.
"""

from __future__ import print_function

import json

from six import string_types

from zope.interface import implementer

from twisted.test.proto_helpers import StringTransport, MemoryReactor

from twisted.internet.address import IPv4Address
from twisted.internet.error import ConnectionDone
from twisted.internet.defer import succeed

from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from twisted.python.urlpath import URLPath

from twisted.python.failure import Failure

import treq

from mimic.resource import get_site


class AbortableStringTransport(StringTransport):
    """
    A :obj:`StringTransport` that supports ``abortConnection``.
    """

    def abortConnection(self):
        """
        Since all connection cessation is immediate in this in-memory
        transport, just call ``loseConnection``.
        """
        self.loseConnection()


class RequestTraversalAgent(object):
    """
    :obj:`IAgent` implementation that issues an in-memory request rather than
    going out to a real network socket.
    """

    def __init__(self, testCase, rootResource):
        """
        :param testCase: A trial synchronous test case to perform assertions
            with.
        :param rootResource: The twisted IResource at the root of the resource
            tree.
        """
        self._memoryReactor = MemoryReactor()
        self._realAgent = Agent(reactor=self._memoryReactor)
        self._testCase = testCase
        self._rootResource = rootResource

    def request(self, method, uri, headers=None, bodyProducer=None):
        """
        Implement IAgent.request.
        """
        # We want to use Agent to parse the HTTP response, so let's ask it to
        # make a request against our in-memory reactor.
        response = self._realAgent.request(method, uri, headers, bodyProducer)

        # That will try to establish an HTTP connection with the reactor's
        # connectTCP method, and MemoryReactor will place Agent's factory into
        # the tcpClients list.  We'll extract that.
        host, port, factory, timeout, bindAddress = (
            self._memoryReactor.tcpClients[0])

        # Then we need to convince that factory it's connected to something and
        # it will give us a protocol for that connection.
        protocol = factory.buildProtocol(None)

        # We want to capture the output of that connection so we'll make an
        # in-memory transport.
        clientTransport = AbortableStringTransport()

        # When the protocol is connected to a transport, it ought to send the
        # whole request because callers of this should not use an asynchronous
        # bodyProducer.
        protocol.makeConnection(clientTransport)

        # Get the data from the request.
        requestData = clientTransport.io.getvalue()

        # Now time for the server to do its job.  Ask it to build an HTTP
        # channel.
        channel = get_site(self._rootResource).buildProtocol(None)

        # Connect the channel to another in-memory transport so we can collect
        # the response.
        serverTransport = StringTransport()
        serverTransport.hostAddr = IPv4Address('TCP', '127.0.0.1', 80)
        channel.makeConnection(serverTransport)

        # Feed it the data that the Agent synthesized.
        channel.dataReceived(requestData)

        # Tell it that the connection is now complete so it can clean up.
        channel.connectionLost(Failure(ConnectionDone()))

        # Now we have the response data, let's give it back to the Agent.
        protocol.dataReceived(serverTransport.io.getvalue())

        # By now the Agent should have all it needs to parse a response.
        protocol.connectionLost(Failure(ConnectionDone()))

        # Return the response in the accepted format (Deferred firing
        # IResponse).  This should be synchronously fired, and if not, it's the
        # system under test's problem.
        return response


@implementer(IBodyProducer)
class SynchronousProducer(object):
    """
    An IBodyProducer which produces its entire payload immediately.
    """

    def __init__(self, body):
        """
        Create a synchronous producer with some bytes.
        """
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        """
        Immediately produce all data.
        """
        consumer.write(self.body)
        return succeed(None)

    def stopProducing(self):
        """
        No-op.
        """


def request(testCase, rootResource, method, uri, body=b"",
            baseURI='http://localhost:8900/',
            headers=None):
    """
    Issue a request and return a synchronous response.
    """
    # allow for relative or absolute URIs, since we're going to the same
    # resource no matter what
    if headers is not None:
        headers_object = Headers()
        for key, value in headers.items():
            headers_object.setRawHeaders(key, value)
    else:
        headers_object = None
    return (
        RequestTraversalAgent(testCase, rootResource)
        .request(method, str(URLPath.fromString(baseURI).click(uri)),
                 bodyProducer=SynchronousProducer(body),
                 headers=headers_object)
    )


def request_with_content(testCase, rootResource, method, uri, body=b"",
                         baseURI='http://localhost:8900/'):
    """
    Issue a request with a body (if there's a body at all) and return
    synchronously with a tuple of ``(response, response body)``
    """
    d = request(testCase, rootResource, method, uri, body, baseURI)

    def get_body(response):
        body_d = treq.content(response)
        body_d.addCallback(lambda body: (response, body))
        return body_d

    return d.addCallback(get_body)


def json_request(testCase, rootResource, method, uri, body=b"",
                 baseURI='http://localhost:8900/', headers=None):
    """
    Issue a request with a JSON body (if there's a body at all) and return
    synchronously with a tuple of ``(response, JSON response body)``
    """
    if not isinstance(body, string_types):
        body = json.dumps(body)

    d = request(testCase, rootResource, method, uri, body, baseURI, headers)

    def get_body(response):
        body_d = treq.json_content(response)
        body_d.addCallback(lambda body: (response, body))
        return body_d

    return d.addCallback(get_body)


def validate_link_json(testCase, json_containing_links):
    """
    Ensure that a JSON blob has the keys "id" and "links", and that the value
    for links is a list of dicts containing 'href' and 'rel'

    :param TestCase testCase: a test case to call assertions on
    :param dict json_content: A dictionary to validate that it has a correct
        'links' attribute.
    """
    testCase.assertIsInstance(json_containing_links, dict,
                              "{0} is not a dictionary"
                              .format(json_containing_links))
    testCase.assertIn('id', json_containing_links,
                      'There is no "id" attribute in {0}'
                      .format(json_containing_links))
    testCase.assertIn('links', json_containing_links,
                      'There is no "links" attribute in {0}'
                      .format(json_containing_links))
    testCase.assertIsInstance(json_containing_links['links'], list,
                              "Links is not a list in {0}"
                              .format(json_containing_links))
    for link in json_containing_links['links']:
        testCase.assertIn('href', link,
                          'Link does not contain "href": {0}'.format(link))
        testCase.assertIn('rel', link,
                          'Link does not contain "rel": {0}'.format(link))
        testCase.assertIsInstance(link['href'], basestring,
                                  '"href" is not a string: {0}'.format(link))
        testCase.assertIsInstance(link['rel'], basestring,
                                  '"rel" is not a string: {0}'.format(link))
