"""
Model objects for the Heat mimic.
"""

from characteristic import attributes, Attribute
import json
from random import randrange

from mimic.model.behaviors import BehaviorRegistryCollection, EventDescription


@attributes(['collection', 'stack_name',
             Attribute('stack_id',
                       default_factory=lambda: Stack.generate_stack_id()),
             Attribute('action', default_factory=lambda: Stack.CREATE),
             Attribute('status', default_factory=lambda: Stack.COMPLETE),
             Attribute('tags', default_factory=list)])
class Stack(object):
    """
    A :obj:`Stack` is a representation of a Heat stack.
    """

    ACTIONS = (
        CREATE, DELETE, UPDATE, ROLLBACK, SUSPEND, RESUME, ADOPT,
        SNAPSHOT, CHECK, RESTORE
    ) = (
        'CREATE', 'DELETE', 'UPDATE', 'ROLLBACK', 'SUSPEND', 'RESUME', 'ADOPT',
        'SNAPSHOT', 'CHECK', 'RESTORE'
    )

    STATUSES = (IN_PROGRESS, FAILED, COMPLETE
                ) = ('IN_PROGRESS', 'FAILED', 'COMPLETE')

    def links_json(self, absolutize_url):
        """
        Create a JSON-serializable data structure describing the links to this
        stack.

        :param callable absolutize_url: see :obj:`default_create_behavior`.
        """
        tid = self.collection.tenant_id
        sid = self.stack_id
        sname = self.stack_name
        href = absolutize_url("v1/{0}/stacks/{1}/{2}".format(tid, sname, sid))
        return [{"href": href, "rel": "self"}]

    def json(self, absolutize_url):
        """
        Returns the JSON representation of the stack.
        """
        return {
            'stack_name': self.stack_name,
            'stack_status': self.action + '_' + self.status,
            'id': self.stack_id,
            'tags': ','.join(self.tags),
            'links': self.links_json(absolutize_url),
            'creation_time': 'Not implemented',
            'updated_time': 'Not implemented',
            'stack_status_reason': 'Not implemented',
            'description': 'Not implemented',
        }

    def update_action(self, action):
        """
        Updates the action of a stack.
        """
        if action not in self.ACTIONS:
            raise ValueError("Action %s not in %s" % (action, self.ACTIONS))

        self.action = action
        return self

    def update_status(self, status):
        """
        Updates the status of a stack.
        """
        if status not in self.STATUSES:
            raise ValueError("Status %s not in %s" % (status, self.STATUSES))

        self.stack = status
        return self

    def update_action_and_status(self, action, status):
        """
        Convenience method for updating action and status.
        """
        return self.update_action(action).update_status(status)

    def is_deleted(self):
        """
        Checks if stack is in a successfully deleted state.
        """
        return self.action == self.DELETE and self.status == self.COMPLETE

    def has_tag(self, tag):
        """
        Checks if stack has a tag.
        """
        return tag in self.tags

    @classmethod
    def generate_stack_id(cls):
        """
        Generates a stack ID.
        """
        return 'test-stack{0}-id-{0}'.format(str(randrange(9999999999)))

    @classmethod
    def from_creation_request_json(cls, collection, creation_json):
        """
        Creates a :obj:`Stack` and adds it to a collection.
        """
        def get_tags():
            tags = creation_json.get('tags', None)
            return tags.split(',') if tags else []

        stack = cls(
            collection=collection,
            stack_name=creation_json['stack_name'],
            tags=get_tags()
        )
        collection.stacks.append(stack)
        return stack

    def creation_response_json(self, absolutize_url):
        """
        Returns the response associated with the stack's creation.
        """
        return {
            "stack": {
                "id": self.stack_id,
                "links": self.links_json(absolutize_url)
            }
        }


stack_creation = EventDescription()
stack_deletion = EventDescription()


@stack_creation.declare_default_behavior
def default_create_behavior(collection, request, body, absolutize_url):
    """
    Successfully create a stack.
    """
    new_stack = Stack.from_creation_request_json(collection, body)
    response = new_stack.creation_response_json(absolutize_url)
    request.setResponseCode(201)
    return json.dumps(response)


@stack_deletion.declare_default_behavior
def default_delete_behavior(collection, request, stack_name, stack_id):
    """
    Successfully delete a stack as long as it exists. Updates the stacks status.
    """
    stack = collection.stack_by_id(stack_id)

    if not stack:
        request.setResponseCode(404)
        return b''

    stack.update_action_and_status(Stack.DELETE, Stack.COMPLETE)
    request.setResponseCode(204)
    return b''


@attributes(
    ["tenant_id", "region_name",
     Attribute("stacks", default_factory=list),
     Attribute(
         "behavior_registry_collection",
         default_factory=lambda: BehaviorRegistryCollection())]
)
class RegionalStackCollection(object):
    """
    A collection of :obj:`Stack` objects for a region.
    """
    def stack_by_id(self, stack_id):
        """
        Retrieves a stack by its ID
        """
        for stack in self.stacks:
            if stack.stack_id == stack_id:
                return stack

    def request_list(self, absolutize_url, show_deleted=False, tags=[]):
        """
        Tries a stack list operation.
        """
        def should_show_stack(stack):
            """
            Determines if a stack should be shown for the list response.
            """
            if stack.is_deleted() and not show_deleted:
                return False

            for tag in tags:
                if not stack.has_tag(tag):
                    return False

            return True

        result = {
            "stacks": [stack.json(absolutize_url) for stack in self.stacks
                       if should_show_stack(stack)]
        }

        return json.dumps(result)

    def request_creation(self, request, body, absolutize_url):
        """
        Tries a stack create operation.
        """
        registry = self.behavior_registry_collection.registry_by_event(
            stack_creation)
        behavior = registry.behavior_for_attributes({
            'tenant_id': self.tenant_id,
            'stack_name': body['stack_name']
        })

        return behavior(collection=self, request=request, body=body,
                        absolutize_url=absolutize_url)

    def request_deletion(self, request, stack_name, stack_id):
        """
        Tries a stack delete operation.
        """
        registry = self.behavior_registry_collection.registry_by_event(
            stack_deletion)
        behavior = registry.behavior_for_attributes({
            'tenant_id': self.tenant_id,
            'stack_name': stack_name,
            'stack_id': stack_id
        })

        return behavior(collection=self, request=request, stack_name=stack_name,
                        stack_id=stack_id)


@attributes(["tenant_id",
             Attribute("regional_collections", default_factory=dict)])
class GlobalStackCollections(object):
    """
    A set of :obj:`RegionalStackCollection` objects owned by a tenant.
    """
    def collection_for_region(self, region_name):
        """
        Retrieves a :obj:`RegionalStackCollection` for a region.
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalStackCollection(tenant_id=self.tenant_id,
                                        region_name=region_name)
            )
        return self.regional_collections[region_name]
