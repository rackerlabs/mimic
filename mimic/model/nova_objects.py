from characteristic import attributes, Attribute
from random import randrange
from twisted.python.urlpath import URLPath
from mimic.util.helper import seconds_to_timestamp

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

    def links_json(self):
        """
        
        """
        def url(suffix):
            return str(URLPath.fromString(
                self.collection.uri_prefix).child(suffix))
        tenant_id = self.collection.tenant_id
        server_id = self.server_id
        return [
            {
                "href": url("v2/{0}/servers/{1}".format(
                    tenant_id, server_id
                )),
                "rel": "self"
            },
            {
                "href": url("{0}/servers/{1}".format(tenant_id, server_id)),
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
                "link": [
                    {
                        
                    }
                ]
}
            {}
        })

    def creation_response_json(self):
        """
        
        """
        return {
            'server': {
                "OS-DCF:diskConfig": self.disk_config,
                "id": s_cache[server_id]['id'],
                "links": s_cache[server_id]['links'],
                "adminPass": "testpassword"
            }
        }


@attributes(["address"])
class IPv4Address(object):
    """
    
    """

    def json(self):
        """
        
        """
        return {"addr": self.address, "version": 4}


@attributes(["address"])
class IPv6Address(object):
    """
    
    """

    def json(self):
        """
        
        """
        return {"addr": self.address, "version": 6}



def default_create_behavior(collection, http, json,
                            ipsegment=lambda: randrange(255)):
    """
    Default behavior in response to a server creation.

    :param ipsegment: A hook provided for IP generation so the IP addresses in
        tests are deterministic; normally a random number between 0 and 255.
    """
    now = collection.clock.seconds()
    server = Server(
        collection=collection,
        server_name=json['name'],
        server_id='test-server{0}-id-{0}'.format(str(randrange(9999999999))),
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
        image_ref=json['imageRef'],
        disk_config=json['OS-DCF:diskConfig'],
    )
    collection.add_server(server)
    return server.creation_response_json()


@attributes(["tenant_id", "region_name", "clock",
             "uri_prefix", Attribute("servers", default_factory=list)])
class RegionalServerCollection(object):
    """
    A collection of servers, in a given region, for a given tenant.

    :ivar uri_prefix: The URL which points at this tenant/region collection of
        servers, *not* including 
    """

    def request_creation(self, creation_http_request, creation_json):
        """
        
        """
        behavior = metadata_to_creation_behavior(
            creation_json.get('metadata'))
        if behavior is None:
            behavior = self.registered_behavior(creation_http_request,
                                                creation_json)
        if behavior is None:
            behavior = default_create_behavior
        return behavior(self, creation_http_request, creation_json)
