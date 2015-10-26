import json
import treq

from twisted.trial.unittest import SynchronousTestCase

from mimic.model.heat_objects import RegionalStackCollection, Stack
from mimic.rest.heat_api import HeatApi
from mimic.test.fixtures import APIMockHelper
from mimic.test.helpers import request


class HeatObjectTests(SynchronousTestCase):
    def setUp(self):
        """
        Test initialization.
        """
        self.coll = RegionalStackCollection(tenant_id='tenant123',
                                            region_name='XYZ')
        self.stack = Stack(stack_name='foo', collection=self.coll)

    def test_update_stack_action(self):
        """
        Tests incorrect action update.
        """
        self.assertRaises(ValueError, self.stack.update_action, 'foo')

    def test_update_stack_status(self):
        """
        Tests incorrect status update.
        """
        self.assertRaises(ValueError, self.stack.update_status, 'foo')

    def test_links_json(self):
        """
        Test correctness of stack links.
        """
        prefix = 'http://foo.bar/baz/'
        href = prefix + 'v1/%s/stacks/%s/%s' % (
            self.coll.tenant_id, self.stack.stack_name, self.stack.stack_id)

        self.assertEqual(self.stack.links_json(lambda suffix: prefix + suffix),
                         [{'href': href, 'rel': 'self'}])


class HeatAPITests(SynchronousTestCase):
    def get_responsebody(self, r):
        """
        Util for getting JSON response body.
        """
        return self.successResultOf(treq.json_content(r))

    def query_string(self, query_params=None):
        """
        Util for building a query string from a parameter mapping.
        """
        return ('?' + '&'.join([k + '=' + v for (k, v) in query_params.items()])
                if query_params else '')

    def list_stacks(self, query_params=None):
        """
        Return a stack list, asserting that the request was successful.
        """
        query = self.query_string(query_params)
        req = request(self, self.root, b"GET", self.uri + '/stacks' + query)
        resp = self.successResultOf(req)
        self.assertEqual(resp.code, 200)
        data = self.get_responsebody(resp)
        return data

    def create_stack(self, stack_name, tags=None):
        """
        Request stack create, assert that the request was successful, and return
        the response.
        """
        req_body = {'stack_name': stack_name}

        if tags:
            req_body['tags'] = ','.join(tags)

        req = request(self, self.root, b"POST", self.uri + '/stacks',
                      body=json.dumps(req_body).encode("utf-8"))
        resp = self.successResultOf(req)
        self.assertEqual(resp.code, 201)
        data = self.get_responsebody(resp)
        return data

    def delete_stack(self, stack_name, stack_id, resp_code=204):
        """
        Request stack delete and assert that the response matched the one
        provided.
        """
        req = request(self, self.root, b"DELETE",
                      '%s/stacks/%s/%s' % (self.uri, stack_name, stack_id))
        resp = self.successResultOf(req)
        self.assertEqual(resp.code, resp_code)

    def setUp(self):
        """
        Test initialization.
        """
        helper = APIMockHelper(self, [HeatApi()])
        self.root = helper.root
        self.uri = helper.uri

    def test_list_stacks_empty(self):
        """
        Test stack list, ensuring correct JSON response.
        """
        resp = self.list_stacks()
        self.assertEqual(resp, {'stacks': []})

    def test_create_stack(self):
        """
        Test stack creation, ensuring correct JSON response.
        """
        foo_resp = self.create_stack('foostack')
        self.assertEqual(set(foo_resp['stack'].keys()), set(['id', 'links']))

    def test_create_stack_id_unique(self):
        """
        Test uniqueness of created stack IDs.
        """
        foo_resp = self.create_stack('foostack')
        bar_resp = self.create_stack('barstack')
        self.assertNotEqual(foo_resp['stack']['id'], bar_resp['stack']['id'])

    def test_list_stacks_one(self):
        """
        Test stack list output for one stack.
        """
        foo_resp = self.create_stack('foostack')
        foo_stack_list = self.list_stacks()['stacks']

        self.assertTrue(len(foo_stack_list), 1)
        self.assertEqual(foo_stack_list[0]['id'], foo_resp['stack']['id'])
        self.assertEqual(foo_stack_list[0]['stack_name'], 'foostack')
        self.assertEqual(
            set(foo_stack_list[0].keys()),
            set([
                'creation_time',
                'description',
                'id',
                'links',
                'stack_name',
                'stack_status',
                'stack_status_reason',
                'tags',
                'updated_time',
            ]))

    def test_list_stacks_two(self):
        """
        Test stack list output for two stacks.
        """
        self.create_stack('foostack')
        self.create_stack('barstack')

        two_stack_list = self.list_stacks()['stacks']
        self.assertEqual(set(stack['stack_name'] for stack in two_stack_list),
                         set(['foostack', 'barstack']))

    def test_delete_stack(self):
        """
        Test stack deletion.
        """
        self.create_stack('foostack')
        bar_resp = self.create_stack('barstack')
        self.create_stack('bazstack')
        self.delete_stack('barstack', bar_resp['stack']['id'])
        new_stack_list = self.list_stacks()['stacks']
        self.assertTrue(len(new_stack_list), 2)

    def test_delete_stack_not_found(self):
        """
        Test correct response from attempting to delete nonexistent stack.
        """
        self.delete_stack('nonexistent', 'bad_id', resp_code=404)

    def test_list_deleted_stacks(self):
        """
        Test listing stacks, including those that have been deleted.
        """
        foo_resp = self.create_stack('foostack')
        self.create_stack('barstack')
        self.delete_stack('foostack', foo_resp['stack']['id'])

        stack_list = self.list_stacks({'show_deleted': 'True'})['stacks']
        self.assertTrue(len(stack_list), 2)

    def test_create_stack_tags(self):
        """
        Test creation of stacks with varying tags.
        """
        self.create_stack('zero_stack')
        self.create_stack('one_stack', tags=['one'])
        self.create_stack('two_stack', tags=['first', 'second'])

        stack_list = self.list_stacks()['stacks']
        self.assertEqual(stack_list[0]['tags'], '')
        self.assertEqual(stack_list[1]['tags'], 'one')
        self.assertEqual(stack_list[2]['tags'], 'first,second')

    def test_list_stack_tags(self):
        """
        Test listing of stacks with various tag combinations.
        """
        foobar_tags = ['foo', 'bar']
        barbaz_tags = ['bar', 'baz']
        self.create_stack('zero_stack')
        self.create_stack('foobar_stack', tags=foobar_tags)
        self.create_stack('barbaz_stack', tags=barbaz_tags)

        foo_stack_list = self.list_stacks({'tags': 'foo'})['stacks']
        bar_stack_list = self.list_stacks({'tags': 'bar'})['stacks']
        baz_stack_list = self.list_stacks({'tags': 'baz'})['stacks']
        foobar_stack_list = self.list_stacks({'tags': 'foo,bar'})['stacks']
        foobaz_stack_list = self.list_stacks({'tags': 'foo,baz'})['stacks']
        wrong_stack_list = self.list_stacks({'tags': 'f'})['stacks']
        another_wrong_stack_list = self.list_stacks({'tags': 'o,b'})['stacks']

        self.assertEqual(len(foo_stack_list), 1)
        self.assertEqual(foo_stack_list[0]['stack_name'], 'foobar_stack')

        self.assertEqual(len(bar_stack_list), 2)
        self.assertEqual(bar_stack_list[0]['stack_name'], 'foobar_stack')
        self.assertEqual(bar_stack_list[1]['stack_name'], 'barbaz_stack')

        self.assertEqual(len(baz_stack_list), 1)
        self.assertEqual(baz_stack_list[0]['stack_name'], 'barbaz_stack')

        self.assertEqual(len(foobar_stack_list), 1)
        self.assertEqual(foobar_stack_list[0]['stack_name'], 'foobar_stack')

        self.assertEqual(len(foobaz_stack_list), 0)
        self.assertEqual(len(wrong_stack_list), 0)
        self.assertEqual(len(another_wrong_stack_list), 0)

    def test_template_validate(self):
        """
        Test template validation, ensuring correct JSON response.
        """
        req_bodies = {'url': {'template_url': "http://bogus.url/here"},
                      'inline': {'template': "http://bogus.url/here"},
                      'wrong': {}}

        requests = dict(
            (key, request(self, self.root, b"POST", self.uri + '/validate',
                          body=json.dumps(body).encode("utf-8")))
            for (key, body) in req_bodies.items()
        )

        responses = dict(
            (key, self.successResultOf(req)) for (key, req) in requests.items()
        )

        resp_bodies = dict(
            (key, self.get_responsebody(resp))
            for (key, resp) in responses.items() if key != 'wrong')

        self.assertEqual(responses['url'].code, 200)
        self.assertEqual(responses['inline'].code, 200)
        self.assertEqual(responses['wrong'].code, 400)

        self.assertTrue('Parameters' in resp_bodies['url'])
        self.assertTrue('Parameters' in resp_bodies['inline'])
