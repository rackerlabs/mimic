"""
Defines the preset values in the mimic api.
"""

get_presets = {"loadbalancers": {"lb_building": "On create load balancer, keeps the load balancer in "
                                                "building state for given seconds",
                                 "lb_error_state": "Puts the LB in error state, and such an LB can only"
                                                   "be deleted",
                                 "lb_pending_update": "Changes the load balancer to PENDING-UPDATE"
                                                      "state for the given number of seconds, any action"
                                                      "other than delete is performed on the server",
                                 "lb_pending_delete": "Changes the load balancer to PENDING-DELETE"
                                                      "state for the given seconds, when deleted"},
               "servers": {"create_server_failure": "{\"message\": \"given message\","
                                                    "\"code\": given code}",
                           "delete_server_failure": "{\"code\": given code,"
                                                    "\"times\": returns given code that many times}",
                           "invalid_image_ref": ["INVALID-IMAGE-ID", "1111", "image_ends_with_Z"],
                           "invalid_flavor_ref": ["INVALID-FLAVOR-ID", "8888", "-4", "1"],
                           "server_error": "sets server state to error on create",
                           "server_building": "sets the server to be in building state for given time"
                                              " in seconds"},
               "identity": {
                   # On ``validate_token`` the tokens listed below
                   # result in 'monitoring-service-admin' impersonator role.
                   "maas_admin_roles": [
                       "this_is_an_impersonator_token",
                       "this_is_an_impersonator_token_also",
                       "impersonate_watson",
                       "impersonate_creator",
                       "this_is_an_impersonator_token_also_2",
                       "impersonate_foo_token"],
                   # On ``validate_token`` the tokens listed below
                   # result in 'racker' impersonator role.
                   "racker_token": ["this_is_a_racker_token"],
                   # Tenants with user observer role
                   "observer_role": ["09876"],
                   # Tenants with user creator role
                   "creator_role": ["09090"],
                   # Tenants with user admin role
                   "admin_role": ["9999"],
                   # Tenants with this token result in a 401 when validating the token
                   "token_fail_to_auth": ["never-cache-this-and-fail-to-auth"],
                   # Users presenting these tokens have contact IDs that correspond
                   # to presets in the Valkyrie plugin...
                   "non_dedicated_observer": ["OneTwo"],
                   "non_dedicated_admin": ["ThreeFour"],
                   "dedicated_full_device_permission_holder": ["HybridOneTwo"],
                   "dedicated_account_permission_holder": ["HybridThreeFour"],
                   "dedicated_limited_device_permission_holder": ["HybridFiveSix"],
                   "dedicated_other_account_observer": ["HybridSevenEight"],
                   "dedicated_other_account_admin": ["HybridNineZero"]}}
