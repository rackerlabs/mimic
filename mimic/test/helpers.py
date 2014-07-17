"""
Helper objects for tests, mostly to allow testing HTTP routes.
"""

from __future__ import print_function

import json

from zope.interface import implementer

from twisted.test.proto_helpers import StringTransport, MemoryReactor

from twisted.internet.address import IPv4Address
from twisted.internet.error import ConnectionDone
from twisted.internet.defer import succeed

from twisted.web.client import Agent
from twisted.web.server import Site
from twisted.web.iweb import IBodyProducer
from twisted.python.urlpath import URLPath

from twisted.python.failure import Failure

import treq


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
        clientTransport = StringTransport()

        # When the protocol is connected to a transport, it ought to send the
        # whole request because callers of this should not use an asynchronous
        # bodyProducer.
        protocol.makeConnection(clientTransport)

        # Get the data from the request.
        requestData = clientTransport.io.getvalue()

        # Now time for the server to do its job.  Ask it to build an HTTP
        # channel.
        channel = Site(self._rootResource).buildProtocol(None)

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
            baseURI='http://localhost:8900/'):
    """
    Issue a request and return a synchronous response.
    """
    # allow for relative or absolute URIs, since we're going to the same
    # resource no matter what
    return (
        RequestTraversalAgent(testCase, rootResource)
        .request(method, str(URLPath.fromString(baseURI).click(uri)),
                 bodyProducer=SynchronousProducer(body))
    )


def json_request(testCase, rootResource, method, uri, body=b"",
                 baseURI='http://localhost:8900/'):
    """
    Issue a request with a JSON body (if there's a body at all) and return
    synchronously with a tuple of the the response along with the JSON body
    """
    if body != "":
        body = json.dumps(body)

    d = request(testCase, rootResource, method, uri, body, baseURI)

    def get_body(response):
        body_d = treq.json_content(response)
        body_d.addCallback(lambda body: (response, body))
        return body_d

    return d.addCallback(get_body)
