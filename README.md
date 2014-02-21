# MIMIC #

Mimic is a plug and play light weight service that provides a compatible interface to Openstack Compute, Rackspace implementation of Identity and Cloud Load balancers.

Things mimic helps with:
* fast set-up
* instant response
* enables offline developmenet
* test error or unusual behavior of an api
* Acts as a central repository for mocked responses from services


## Compute ##

1. LIST servers - Lists servers on the tenant in mimic
2. POST server - Creates a server in mimic *(look at the 'Errors or unusual behaviors supported for compute' below)*
3. GET server - Returns the server, if it exists in mimic else returns a 404
4. DELETE server - Deletes the server, if it exists in mimcic else returns 404
5. LIST addresses - Lists the private and public Ips for the given server. 404 if not found.
6. GET image - If the image ID is anything but what is listed in the mimic presets, `invalid_image_ref`
			   returns 200. Else returns a 400.
7. GET flavor - If the flavor ID is anything but what is listed in the mimic presets, `invalid_flavor_ref`
			   returns 200. Else returns a 400.
8. GET limits - Returns only the absolute limits for compute

#### Errors or unusual behaviors supported for compute: ####
* [mimic_presets](https://github.com/rackerlabs/mimic/blob/master/mimic/canned_responses/mimic_presets.py) *

Based on the metadata provided when a server is being created, a server can be made to behave as follows:
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

## Identity ##
1. Authenticate - Given a tenant id, username and password, returns the service catalog with links to compute and load balancer links within mimic, and a test token.
2. Impersonate user (Admin call) - Given a token created by mimic in the header, returns a test token for the username.
3. GET endpoints - Given token created by mimic, returns the service catalog for that user.


## Cloud Load Balancer ##
1. LIST load balancers - Lists the load balancers created in mimic
2. CREATE load balancer - Creates a load balancer
3. GET load balancer - Returns the load balancer if it exists, else 404
4. DELETE load balancer - Deletes the load balancer if it exists, else returns 404
5. LIST nodes - Lists the nodes on the load balancer
6. CREATE node - Creates a node on the load balancer
7. GET node - Returns the node if it exists, else returns 404
8. DELETE node - Deletes the node if it exists, else returns 404

#### Errors or unusual behaviors supported for cloud load balancers: ####
* [mimic_presets](https://github.com/rackerlabs/mimic/blob/master/mimic/canned_responses/mimic_presets.py) *

Based on the key and val;ue of the metadata provided when a load balancer is being created, a load balancer can be made to behave as follows:
* Remain in 'BUILD' state for the specified amount of time
* Load balancer goes into'PENDING-UPDATE' state on every add/delete node for the specified amout of time
* Load balancer goes into'PENDING-DELETE' state on delete load balancer for the specified amout of time
* Load balancer goes into an error state on creation


## Mimic does not ##:
* support XML
* validate the auth token
