from characteristic import attributes, Attribute
from random import randrange
from json import loads, dumps
from twisted.python.urlpath import URLPath
from mimic.util.helper import seconds_to_timestamp
from mimic.util.helper import invalid_resource

@attributes(["collection", "server_id", "server_name", "metadata",
             "creation_time", "update_time", "public_ips", "private_ips",
             "status", "flavor_ref", "image_ref", "disk_config",
             "admin_password", "creation_request_json"])
class Server(object):
    """
    
    """

    static_defaults = {
        "OS-EXT-STS:power_state": 1,
        "OS-EXT-STS:task_state": None,
        "accessIPv4": "198.101.241.238", # TODO: same as public IP
        "accessIPv6": "2001:4800:780e:0510:d87b:9cbc:ff04:513a",
        "key_name": None,
        "hostId": "33ccb6c82f3625748b6f2338f54d8e9df07cc583251e001355569056",
        "progress": 100,
        "user_id": "170454"
    }

    def url(self, suffix):
        """

        """
        return str(URLPath.fromString(
            self.collection.uri_prefix).child(suffix))

    def links_json(self):
        """
        
        """
        tenant_id = self.collection.tenant_id
        server_id = self.server_id
        return [
            {
                "href": self.url("v2/{0}/servers/{1}"
                                 .format(tenant_id, server_id)),
                "rel": "self"
            },
            {
                "href": self.url("{0}/servers/{1}"
                                 .format(tenant_id, server_id)),
                "rel": "bookmark"
            }
        ]

    def brief_json(self):
        """
        Brief version of this server, for the non-details list servers request.
        """
        return {
            'name': self.server_name,
            'links': self.links_json(),
            'id': self.server_id
        }

    def detail_json(self):
        """
        Long-form JSON-serializable object representation of this server, as
        returned by either a GET on this individual server or a member in the
        list returned by the list-details request.
        """
        template = self.static_defaults.copy()
        template.update({
            "OS-DCF:diskConfig": self.disk_config,
            "OS-EXT-STS:vm_state": self.status,
            "addresses": {
                "private": [addr.json() for addr in self.private_ips],
                "public": [addr.json() for addr in self.public_ips]
            },
            "created": seconds_to_timestamp(self.creation_time),
            "updated": seconds_to_timestamp(self.updated_time),
            "flavor": {
                "id": self.flavor_ref,
                "links": [{"href": self.url(
                    "{0}/flavors/{1}".format(self.tenant_id,
                                             self.flavor_ref))}],
                "rel": "bookmark"
            },
            "image": {
                "id": self.image_ref,
                "links": [{
                    "href": self.url("{0}/images/{1}".format(self.tenant_id,
                                                             self.flavor_ref))
                }]
            }
            if self.image_ref is not None else '',
            "links": self.links_json(),
            "metadata": self.metadata,
            "name": self.name,
            "tenant_id": self.tenant_id,
            "status": self.status
        })

    def creation_response_json(self):
        """
        A JSON-serializable object returned for the initial creation of this
        server.
        """
        return {
            'server': {
                "OS-DCF:diskConfig": self.disk_config,
                "id": self.server_id,
                "links": self.links_json(),
                "adminPass": self.admin_password,
            }
        }

    def from_creation_request_json(self, collection, json,
                                   ipsegment=lambda: randrange(255)):
        """
        Create a :obj:`Server` from a JSON-serializable object that would be in
        the body of a create server request.
        """
        now = collection.clock.seconds()
        return Server(
            collection=collection,
            server_name=json['name'],
            server_id=('test-server{0}-id-{0}'
                       .format(str(randrange(9999999999)))),
            metadata=json.get("metadata") or {},
            created_time=now,
            update_time=now,
            private_ips=[
                IPv4Address("10.180.{0}.{1}".format(ipsegment(), ipsegment())),
            ],
            public_ips=[
                IPv4Address(address="198.101.241.{0}".format(ipsegment())),
                IPv6Address(address="2001:4800:780e:0510:d87b:9cbc:ff04:513a")
            ],
            creation_request_json=json,
            flavor_ref=json['flavorRef'],
            image_ref=json['imageRef'] or '',
            disk_config=json['OS-DCF:diskConfig'],
        )


@attributes(["address"])
class IPv4Address(object):
    """
    An IPv6 address for a server.
    """

    def json(self):
        """
        A JSON-serializable representation of this address.
        """
        return {"addr": self.address, "version": 4}


@attributes(["address"])
class IPv6Address(object):
    """
    An IPv6 address for a server.
    """

    def json(self):
        """
        A JSON-serializable representation of this address.
        """
        return {"addr": self.address, "version": 6}


def default_create_behavior(collection, http, json,
                            ipsegment=lambda: randrange(255)):
    """
    Default behavior in response to a server creation.

    :param ipsegment: A hook provided for IP generation so the IP addresses in
        tests are deterministic; normally a random number between 0 and 255.
    """
    new_server = Server.from_creation_request_json(collection, json, ipsegment)
    response = new_server.creation_response_json()
    return dumps(response)


def metadata_to_creation_behavior(metadata):
    """
    Examine the metadata given to a server creation request, and return a
    behavior based on the values present there.
    """
    if 'create_server_failure' in metadata:
        def fail_and_dont_do_anything(collection, http, json):
            # behavior for failing to even start to build
            failure = loads(metadata['create_server_failure'])
            http.setResponseCode(failure['code'])
            return invalid_resource(failure['message', failure['code']])
    return None


@attributes(["tenant_id", "region_name", "clock",
             "uri_prefix", Attribute("servers", default_factory=list)])
class RegionalServerCollection(object):
    """
    A collection of servers, in a given region, for a given tenant.

    :ivar uri_prefix: The URL which points at this tenant/region collection of
        servers, *not* including the version number (therefore suitable for
        generating bookmark links).
    """

    def registered_creation_behavior(self, creation_http_request,
                                     creation_json):
        """
        Retrieve a behavior that was previously registered via a control plane
        request to inject an error in advance, based on whether it matches the
        parameters in the given creation JSON and HTTP request properties.
        """
        return None

    def request_creation(self, creation_http_request, creation_json):
        """
        Request that a server be created.
        """
        behavior = metadata_to_creation_behavior(
            creation_json.get('metadata'))
        if behavior is None:
            behavior = self.registered_creation_behavior(creation_http_request,
                                                         creation_json)
        if behavior is None:
            behavior = default_create_behavior
        return behavior(self, creation_http_request, creation_json)
