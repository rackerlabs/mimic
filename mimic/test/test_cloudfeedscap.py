"""
Tests for :obj:`mimic.rest.cloudfeedscap`
"""
import json
from datetime import datetime
from urllib import urlencode

import xmltodict

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.rest.cloudfeedscap import CustomerAccessEvent, generate_feed_xml
from mimic.test.helpers import request, request_with_content
from mimic.util.helper import seconds_to_timestamp

from testtools.matchers import MatchesDict, MatchesListwise, Equals, Contains, ContainsDict

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock


empty_feed = ('<feed xmlns="http://www.w3.org/2005/Atom">'
             '<title type="text">customer_access_policy/events</title></feed>')


def assert_has_events(testcase, xml, events, prev, next):
    """
    Assert that xml has given events with previous and next link
    """
    feed_match = MatchesDict(
        {"feed": ContainsDict({
            "link": MatchesListwise([
                MatchesDict({"@href": Equals(prev),
                             "@rel": Equals("previous")}),
                MatchesDict({"@href": Equals(next),
                             "@rel": Equals("next")})
            ]),
            "entry": MatchesListwise([
                ContainsDict({
                    "event:event": ContainsDict({
                        "@tenant_id": Equals(event.tenant_id),
                        "ap:product": ContainsDict({"@status": Equals(event.status)})
                    }),
                    "updated": Equals(seconds_to_timestamp(event.updated)),
                    "published": Equals(seconds_to_timestamp(event.updated))
                })
                for event in events
            ])
        })
    })
    namespaces = {"http://www.w3.org/2005/Atom": None,
                  "http://docs.rackspace.com/core/event": "event",
                  "http://docs.rackspace.com/event/customer/access_policy": "ap"}
    d = xmltodict.parse(xml, process_namespaces=True, namespaces=namespaces)
    testcase.assertIsNone(feed_match.match(d))


def link(params):
    """
    Return full URL with given query params
    """
    return u"https://mimic-host-port/cloudfeeds_cap/customer_access_events?{}".format(urlencode(params))


class GenFeedTests(SynchronousTestCase):
    """
    Tests for :func:`generate_feed`
    """

    def test_no_entries(self):
        """
        Generates empty feed when given empty list of events. Does not provide next and previous links
        """
        self.assertEqual(generate_feed_xml([]), empty_feed)

    def test_entries(self):
        """
        Generates feed with proper next and previous link and "entry" nodes with event info in them.
        Currently only checks if event info i.e. (tenant_id, status, links and updated) are correct.
        Ideally, it should ideally check against XML schema also. Will probably add that later.
        """
        events = [CustomerAccessEvent("t1", "FULL", 0.0, "1"),
                  CustomerAccessEvent("t2", "TERMINATED", 100.0, "2")]
        xml = generate_feed_xml(events)
        assert_has_events(self, xml, events, link(dict(marker="1", direction="forward")),
                          link(dict(marker="2", direction="backward")))


class RoutesTests(SynchronousTestCase):
    """
    Test for routes in :obj:`CloudFeedsCAPRoutes`
    """
    def setUp(self):
        self.clock = Clock()
        self.core = MimicCore(self.clock, [])
        self.root = MimicRoot(self.core, clock=self.clock).app.resource()
        from mimic.rest import cloudfeedscap as cf
        self.ids = ["id2", "id1"]
        self.patch(cf, "uuid4", lambda: self.ids.pop())

    def test_add_events_empty(self):
        """
        Calling `POST ../events` first time will add events in event store and setup
        indexes
        """
        events = [{"tenant_id": "1234", "status": "SUSPENDED"},
                  {"tenant_id": "2345", "status": "FULL"}]
        d = request(self, self.root, "POST", "/cloudfeeds_cap/events",
                    body=json.dumps({"events": events}).encode("utf-8"))
        self.assertEqual(self.successResultOf(d).code, 201)
        self.assertEqual(
            self.core.cloudfeeds_ca_store.events,
            [CustomerAccessEvent(u"1234", u"SUSPENDED", 0.0, u"id1"),
             CustomerAccessEvent(u"2345", u"FULL", 0.0, u"id2")])
        self.assertEqual(
            self.core.cloudfeeds_ca_store.events_index, {"id1": 0, "id2": 1})

    def test_add_events_update(self):
        """
        Calling `POST .../events` with existing events will prepend the events
        to the store.events list and update the store.events_index too
        """
        self.test_add_events_empty()
        self.clock.advance(200)
        self.ids = ["id5", "id4"]
        events = [{"tenant_id": "t1", "status": "TERMINATED"},
                  {"tenant_id": "t2", "status": "SUSPENDED"}]
        d = request(self, self.root, "POST", "/cloudfeeds_cap/events",
                    body=json.dumps({"events": events}).encode("utf-8"))
        self.assertEqual(self.successResultOf(d).code, 201)
        exp_events = [CustomerAccessEvent(u"t1", u"TERMINATED", 200.0, u"id4"),
                      CustomerAccessEvent(u"t2", u"SUSPENDED", 200.0, u"id5"),
                      CustomerAccessEvent(u"1234", u"SUSPENDED", 0.0, u"id1"),
                      CustomerAccessEvent(u"2345", u"FULL", 0.0, u"id2")]
        self.assertEqual(self.core.cloudfeeds_ca_store.events, exp_events)
        self.assertEqual(
            self.core.cloudfeeds_ca_store.events_index,
            {"id4": 0, "id5": 1, "id1": 2, "id2": 3})
        return exp_events

    def test_get_events_empty(self):
        """
        `GET ../customer_access_policy/events` returns empty xml feed when there
        are no events stored. No previous and next links are provided.
        """
        d = request_with_content(
            self, self.root, "GET", "/cloudfeeds_cap/customer_access_policy/events")
        resp, body = self.successResultOf(d)
        self.assertEqual(body, empty_feed)

    def test_get_events(self):
        """
        `GET ../customer_access_policy/events` returns events stored in xml feed
        format with proper next and previous link
        """
        events = self.test_add_events_update()
        resp, body = self.successResultOf(request_with_content(
            self, self.root, "GET", "/cloudfeeds_cap/customer_access_policy/events"))
        assert_has_events(
            self, body, events, link(dict(marker="id4", direction="forward")),
            link(dict(marker="id2", direction="backward")))

    def test_get_events_marker_forward(self):
        """
        `GET ../customer_access_policy/events?marker=m&direction=forward` returns events occurring
        after given marker
        """
        events = self.test_add_events_update()
        resp, body = self.successResultOf(request_with_content(
            self, self.root, "GET",
            "/cloudfeeds_cap/customer_access_policy/events?marker=id1&direction=forward"))
        assert_has_events(
            self, body, events[:2],
            link(dict(marker="id4", direction="forward")),
            link(dict(marker="id5", direction="backward")))

    def test_get_events_marker_backward(self):
        """
        `GET ../customer_access_policy/events?marker=m&direction=backward` returns events occurring
        before given marker
        """
        events = self.test_add_events_update()
        resp, body = self.successResultOf(request_with_content(
            self, self.root, "GET",
            "/cloudfeeds_cap/customer_access_policy/events?marker=id1&direction=backward"))
        assert_has_events(
            self, body, events[2:],
            link(dict(marker="id1", direction="forward")),
            link(dict(marker="id2", direction="backward")))

    def test_get_events_limit(self):
        """
        `GET ../customer_access_policy/events?limit=3` returns events <= 3
        """
        events = self.test_add_events_update()
        resp, body = self.successResultOf(request_with_content(
            self, self.root, "GET",
            "/cloudfeeds_cap/customer_access_policy/events?limit=3"))
        assert_has_events(
            self, body, events[:3],
            link(dict(marker="id4", direction="forward")),
            link(dict(marker="id1", direction="backward")))
