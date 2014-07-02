Documentation Documentation
===========================

Here are some things we're going to document and how we're going to document them.

There should be a document describing how to write your own API mock plugin.

- reference the `Twisted documentation for writing plugins
  <https://twistedmatrix.com/documents/current/core/howto/plugin.html>`_ as a
  prerequisite

- provide an example of the file that goes into `mimic/plugins`,
  `dummy_plugin.py` is a good start but it fails to explain what a real
  resource might look like that responds to API requests

  - unlike `dummy_plugin.py`, the `IAPIMock` implementer class ought to live in
    an application module, the plugin should only contain the instantiation.

  - better naming might help explain why you have to make separate "API mock"
    and "Region" objects.

- explain what a twisted web resource is, reference twisted docs for the
  interface and klein docs for how to produce your own resource with nice route
  decorators

- implement catalog_entries

  - are you implementing a crazy endpoint that manipulates the tenant ID?
    manipulate it here.

    - remember tenant ID may be None, because the core needs to allocate URI
      prefixes before there are any tenants.  maybe this really ought to be a
      different API; the difference in meaning is that
      ``catalog_entries(None)`` must enumerate all regions that any user might
      possibly ever be able to access, whereas ``catalog_entries(not_none)``
      can return different regions for different tenants if it wants to (for
      example, simulating limited availability).

      - this is super confusing, and technically unnecessary; it just made the
        implementation slightly easier to do in the first place.  really all
        the URI prefixes could be allocated on demand as individual tenants
        receive particular services/region pairs for the first time, obviating
        the need for this weird implementation detail.  possibly file an issue
        for this and just fix it before writing the final docs so we don't have
        to explain.

  - return entries.  canonical region right now is "ORD" but hopefully we can
    eventually change this API at some point to support a suggested list of
    regions from some configuration, pass in that list and then honor it here.

- implement resource_for_region

  - this gets called on every request

  - guideline: use klein to build your hierarchy since that makes it easier

    - note that you can always use whatever twisted.web resources make sense,
      if you want to toss a static hierarchy in there you don't need to use
      klein, just make a static.File or a static.Data (perhaps note this at the
      end?)

  - to-do implementation-wise: we really ought to have a JSON serializer as a
    decorator or something so everybody doesn't have to actually type
    "``dumps``" all the time

  - note where the "region" is in the hierarchy; there will be some URI prefix
    which you hopefully don't care about (passed in as the
    ``resource_for_region`` argument) but you have to handle all segments from
    the end of the thing that Mimic has allocated for you: including your
    "prefix"; so if your "prefix" to the Endpoint construction in
    ``catalog_entries`` is "v5" then your routes need to all begin
    "/v5/<string:tenant_id>/".  The object returned from _that_ route is
    actually the specific tenant's service endpoint.

  - implementation note: t.w.resource lifecycle management is weird, and a bit
    hard to explain.  It would be nice to tell the developer at this point that
    they can store some kind of state on the session or associated with the
    tenant, but given that each resource is implicitly created with each
    request, it's a bit tricky to do that.  perhaps we should expose the
    "session" object we're already keeping around in MimicCore to application
    code, or a dictionary associated with it, so that we can easily have
    per-tenant state.


