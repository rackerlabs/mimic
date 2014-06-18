

import itertools
from json import dumps as dump_json
from twisted.trial.unittest import TestCase

from mimic.canned_responses.nova import server_template


class ResponseGenerationTests(TestCase):
    """
    Tests for Nova response generation.
    """

    def test_server_template(self):
        """
        :obj:`server_template` generates a JSON object representing an
        individual Nova server.
        """

        input_server_info = {
            "flavorRef": "some_flavor",
            "imageRef": "some_image",
            "name": "some_server_name",
            "metadata": {
                "some_key": "some_value",
                "some_other_key": "some_other_value",
            }
        }

        counter = itertools.count(1)

        compute_service_uri_prefix = (
            "http://mimic.example.com/services/region/compute/"
        )

        actual = server_template("some_tenant", input_server_info,
                                 "some_server_id", "some_status",
                                 "the_current_time",
                                 lambda: next(counter),
                                 compute_service_uri_prefix)

        expectation = {
            "OS-DCF:diskConfig": "AUTO",
            "OS-EXT-STS:power_state": 1,
            "OS-EXT-STS:task_state": None,
            "OS-EXT-STS:vm_state": "active",
            "accessIPv4": "198.101.241.238",
            "accessIPv6": "2001:4800:780e:0510:d87b:9cbc:ff04:513a",
            "key_name": None,
            "addresses": {
                "private": [
                    {
                        "addr": "10.180.1.2",
                        "version": 4
                    }
                ],
                "public": [
                    {
                        "addr": "198.101.241.3",
                        "version": 4
                    },
                    {
                        "addr": "2001:4800:780e:0510:d87b:9cbc:ff04:513a",
                        "version": 6
                    }
                ]
            },
            "created": "the_current_time",
            "flavor": {
                "id": "some_flavor",
                "links": [
                    {
                        "href": ("http://mimic.example.com/services/region/"
                                 "compute/some_tenant/flavors/some_flavor"),
                        "rel": "bookmark"
                    }
                ]
            },
            "hostId": ("33ccb6c82f3625748b6f2338f54d8e9df07cc583251e001355569"
                       "056"),
            "id": "some_server_id",
            "image": {
                "id": "some_image",
                "links": [
                    {
                        "href": "http://mimic.example.com/services/region/"
                        "compute/some_tenant/images/some_image",
                        "rel": "bookmark"
                    }
                ]
            },
            "links": [
                {
                    "href": ("http://mimic.example.com/services/region/"
                             "compute/v2/some_tenant/servers/some_server_id"),
                    "rel": "self"
                },
                {
                    "href": "http://mimic.example.com/services/region/compute/"
                    "some_tenant/servers/some_server_id",
                    "rel": "bookmark"
                }
            ],
            "metadata": {"some_key": "some_value",
                         "some_other_key": "some_other_value"},
            "name": "some_server_name",
            "progress": 100,
            "status": "some_status",
            "tenant_id": "some_tenant",
            "updated": "the_current_time",
            "user_id": "170454"
        }
        self.assertEquals(dump_json(expectation, indent=2),
                          dump_json(actual, indent=2))
