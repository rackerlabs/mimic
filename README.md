# MIMIC #

Mimic is an API-compatible mock service for  __Openstack Compute__ and __Rackspace's implementation of Identity and Cloud Load balancers__. It is backed by in-memory data structure rather than a potentially expensive database.

Mimic helps with:
* fast set-up
* instant response
* cost efficient
* enables offline developmenet
* enables ability to test unusual behaviors/errors of an api
* acts as a central repository for mocked responses from services

### Come join us develop Mimic! Talk to us at ##mimic on irc.freenode.net ###

#### Build status: ####
[![Build Status](https://travis-ci.org/rackerlabs/mimic.svg?branch=master)](https://travis-ci.org/rackerlabs/mimic)

[![Coverage Status](https://coveralls.io/repos/rackerlabs/mimic/badge.png)](https://coveralls.io/r/rackerlabs/mimic)

## Compute ##

#### Calls supported: ####
https://github.com/rackerlabs/mimic/blob/master/mimic/rest/nova_api.py

1. LIST servers - Lists servers on the tenant, in mimic
2. POST server - Creates a server in mimic *(look at the 'Errors or unusual behaviors supported for compute' below)*
3. GET server - Returns the server, if it exists in mimic else returns a 404
4. DELETE server - Deletes the server, if it exists in mimic else returns 404
5. LIST addresses - Lists the private and public Ips for the given server. 404 if not found.
6. GET image - If the image ID is anything but what is listed in the mimic presets, `invalid_image_ref`
			   returns 200. Else returns a 400.
7. GET flavor - If the flavor ID is anything but what is listed in the mimic presets, `invalid_flavor_ref`
			   returns 200. Else returns a 400.
8. GET limits - Returns only the absolute limits for compute

#### Errors or unusual behaviors supported for compute: ####
Based on the metadata ([mimic_presets](https://github.com/rackerlabs/mimic/blob/master/mimic/canned_responses/mimic_presets.py)) provided when a server is being created, a server can be made to behave as follows:
* Fail with the given response message and response code
* Go into an error state on creation
* Remain in building state for the specified amount of time
* Fails to delete the server, with the specified response code for the number of times specified
* Returns 'image not found' or 'flavor not found' responses for specified IDs

Eg:
Request for create server that remains in building for 120 seconds:

`{
    "server" : {
        "name" : "api-test-server-1",
        "imageRef" : "3afe97b2-26dc-49c5-a2cc-a2fc8d80c001",
        "flavorRef" : "2",
        "metadata": {"server_building": 120}
    }
 }`


## Rackspace Auth ##

#### Calls supported: ####
https://github.com/rackerlabs/mimic/blob/master/mimic/rest/auth_api.py

1. Authenticate - Given a tenant id, username and password, returns the service catalog with links to compute and load balancer links within mimic, and a test token.
2. Impersonate user (Admin call) - Given a token created by mimic in the header, returns a test token for the username.
3. GET endpoints - Given token created by mimic, returns the service catalog for that user.


## Cloud Load Balancer ##

#### Calls supported: ####
https://github.com/rackerlabs/mimic/blob/master/mimic/rest/loadbalancer_api.py

1. LIST load balancers - Lists the load balancers created in mimic
2. POST load balancer - Creates a load balancer *(look at the 'Errors or unusual behaviors supported for cloud load balancers' below)*
3. GET load balancer - Returns the load balancer if it exists, else 404
4. DELETE load balancer - Deletes the load balancer if it exists, else returns 404
5. LIST nodes - Lists the nodes on the load balancer
6. POST node - Creates a node on the load balancer
7. GET node - Returns the node if it exists, else returns 404
8. DELETE node - Deletes the node if it exists, else returns 404

#### Errors or unusual behaviors supported for cloud load balancers: ####
Based on key and value of the metadata ([mimic_presets](https://github.com/rackerlabs/mimic/blob/master/mimic/canned_responses/mimic_presets.py)) provided when a load balancer is being created, a load balancer can be made to behave as follows:
* Remain in 'BUILD' state for the specified amount of time
* Load balancer goes into 'PENDING-UPDATE' state on every add/delete node for the specified amout of time
* Load balancer goes into 'PENDING-DELETE' state on delete load balancer for the specified amout of time
* Load balancer goes into an error state on creation

Eg:
Request for create load balancer that is expected to go into 'PENDING-UPDATE' state on every add/delete
node, for 20 seconds:

`{"loadBalancer": {"name": "a-new-loadbalancer2", "protocol": "HTTP", "virtualIps": [{"type": "PUBLIC"}], "metadata": [{"key": "lb_pending_update", "value": 20}], "nodes": []}}`

## Mimic does not: ##
* support XML
* validate the auth token

## Running Mimic on a cloud server ##
1. create a cloud server with an image that by default comes with python 2.7 (eg: ubuntu 12.04) and ssh into it
2. `git clone https://github.com/rackerlabs/mimic.git`
3. `pip install -r requirements.txt` from within the mimic folder (if there is a gcc error, `apt-get install python-dev`)
4. cd into mimic or add the mimic to the PYTHONPATH and run `twistd -n mimic`

## Running Mimic on Docker ##

The repository root has a `Dockerfile` that does what you want. It exposes Mimic on port 8900 by default.

To play around with Mimic locally, try:

```
docker build -t mimic . && docker run --restart=no --rm=true -p 8900:8900 mimic
```

This will expose Mimic on port 8900, so you can access it directly from the host. The default port exposure is intended for communication between containers; see the Docker documentation for more information. If you're using `boot2docker`, run `boot2docker ip` to find the right IP.
