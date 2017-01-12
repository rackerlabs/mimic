"""
Tests for :obj:`mimic.rest.cloudfeedscap`
"""
import json
from datetime import datetime

import xmltodict

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.rest.cloudfeedscap import CustomerAccessEvent, generate_feed_xml
from mimic.test.helpers import request
from mimic.util.helper import seconds_to_timestamp

from testtools.matchers import MatchesDict, MatchesListwise, Equals, Contains, ContainsDict

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock


class GenFeedTests(SynchronousTestCase):
    """
    Tests for :func:`generate_feed`
    """

    def test_no_entries(self):
        """
        Generates empty feed when given empty list of events. Does not provide next and previous links
        """
        self.assertEqual(
            generate_feed_xml([]),
            ('<feed xmlns="http://www.w3.org/2005/Atom">'
             '<title type="text">customer_access_policy/events</title></feed>'))

    def test_entries(self):
        """
        Generates feed with proper next and previous link and "entry" nodes with event info in them.
        Currently only checks if event info i.e. (tenant_id, status, links and updated) are correct.
        Ideally, it should ideally check against XML schema also. Will probably add that later.
        """
        events = [CustomerAccessEvent("t1", "FULL", 0.0, "1"),
                  CustomerAccessEvent("t2", "TERMINATED", 100.0, "2")]
        updates = [seconds_to_timestamp(e.updated) for e in events]
        xml = generate_feed_xml(events)
        namespaces = {"http://www.w3.org/2005/Atom": None,
                      "http://docs.rackspace.com/core/event": "event",
                      "http://docs.rackspace.com/event/customer/access_policy": "ap"}
        d = xmltodict.parse(xml, process_namespaces=True, namespaces=namespaces)
        feed_match = MatchesDict(
            {"feed": ContainsDict({
                "link": MatchesListwise([
                    MatchesDict({"@href": Equals("https://mimic-host-port?marker=1&direction=forward"),
                                 "@rel": Equals("previous")}),
                    MatchesDict({"@href": Equals("https://mimic-host-port?marker=2&direction=backward"),
                                 "@rel": Equals("next")})
                ]),
                "entry": MatchesListwise([
                    ContainsDict({
                        "event:event": ContainsDict({
                            "@tenant_id": Equals("t1"),
                            "ap:product": ContainsDict({"@status": Equals("FULL")})
                        }),
                        "updated": Equals(updates[0]),
                        "published": Equals(updates[0])
                    }),
                    ContainsDict({
                        "event:event": ContainsDict({
                            "@tenant_id": Equals("t2"),
                            "ap:product": ContainsDict({"@status": Equals("TERMINATED")})
                        }),
                        "updated": Equals(updates[1]),
                        "published": Equals(updates[1])
                    })
                ])
            })
        })
        self.assertIsNone(feed_match.match(d))


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
        d = request(self, self.root, "POST", "/customer_access_cloudfeeds/events",
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
        d = request(self, self.root, "POST", "/customer_access_cloudfeeds/events",
                    body=json.dumps({"events": events}).encode("utf-8"))
        self.assertEqual(self.successResultOf(d).code, 201)
        self.assertEqual(
            self.core.cloudfeeds_ca_store.events,
            [CustomerAccessEvent(u"t1", u"TERMINATED", 200.0, u"id4"),
             CustomerAccessEvent(u"t2", u"SUSPENDED", 200.0, u"id5"),
             CustomerAccessEvent(u"1234", u"SUSPENDED", 0.0, u"id1"),
             CustomerAccessEvent(u"2345", u"FULL", 0.0, u"id2")])
        self.assertEqual(
            self.core.cloudfeeds_ca_store.events_index,
            {"id4": 0, "id5": 1, "id1": 2, "id2": 3})
