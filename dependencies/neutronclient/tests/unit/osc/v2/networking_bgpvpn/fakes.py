# Copyright (c) 2016 Juniper Networks Inc.
# All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import copy
from unittest import mock

from openstack.network.v2 import bgpvpn as _bgpvpn
from openstack import resource as sdk_resource
from osc_lib.utils import columns as column_util

from neutronclient.osc import utils as nc_osc_utils
from neutronclient.osc.v2.networking_bgpvpn.resource_association import\
    CreateBgpvpnResAssoc
from neutronclient.osc.v2.networking_bgpvpn.resource_association import\
    DeleteBgpvpnResAssoc
from neutronclient.osc.v2.networking_bgpvpn.resource_association import\
    ListBgpvpnResAssoc
from neutronclient.osc.v2.networking_bgpvpn.resource_association import\
    SetBgpvpnResAssoc
from neutronclient.osc.v2.networking_bgpvpn.resource_association import\
    ShowBgpvpnResAssoc
from neutronclient.osc.v2.networking_bgpvpn.resource_association import\
    UnsetBgpvpnResAssoc
from neutronclient.osc.v2.networking_bgpvpn.router_association import\
    CreateBgpvpnRouterAssoc
from neutronclient.osc.v2.networking_bgpvpn.router_association import\
    SetBgpvpnRouterAssoc
from neutronclient.osc.v2.networking_bgpvpn.router_association import\
    ShowBgpvpnRouterAssoc
from neutronclient.tests.unit.osc.v2 import fakes as test_fakes


_FAKE_PROJECT_ID = 'fake_project_id'


class TestNeutronClientBgpvpn(test_fakes.TestNeutronClientOSCV2):

    def setUp(self):
        super(TestNeutronClientBgpvpn, self).setUp()
        self.neutronclient.find_resource = mock.Mock(
            side_effect=lambda resource, name_or_id, project_id=None,
            cmd_resource=None, parent_id=None, fields=None:
            {'id': name_or_id, 'tenant_id': _FAKE_PROJECT_ID})
        self.neutronclient.find_resource_by_id = mock.Mock(
            side_effect=lambda resource, resource_id, cmd_resource=None,
            parent_id=None, fields=None:
            {'id': resource_id, 'tenant_id': _FAKE_PROJECT_ID})
        nc_osc_utils.find_project = mock.Mock(
            side_effect=lambda _, name_or_id, __: mock.Mock(id=name_or_id))


def create_one_bgpvpn(attrs=None):
    """Create a fake BGP VPN."""

    attrs = attrs or {}

    # Set default attributes.
    bgpvpn_attrs = {
        'id': 'fake_bgpvpn_id',
        'tenant_id': _FAKE_PROJECT_ID,
        'name': '',
        'type': 'l3',
        'route_targets': [],
        'import_targets': [],
        'export_targets': [],
        'route_distinguishers': [],
        'networks': [],
        'routers': [],
        'ports': [],
        'vni': 100,
        'local_pref': 777,
    }

    # Overwrite default attributes.
    bgpvpn_attrs.update(attrs)
    return _bgpvpn.BgpVpn(**bgpvpn_attrs)


def create_bgpvpns(attrs=None, count=1):
    """Create multiple fake BGP VPN."""

    bgpvpns = []
    for i in range(0, count):
        if attrs is None:
            attrs = {'id': 'fake_id%d' % i}
        elif getattr(attrs, 'id', None) is None:
            attrs['id'] = 'fake_id%d' % i
        bgpvpns.append(create_one_bgpvpn(attrs))

    return bgpvpns


class BgpvpnFakeAssoc(object):
    _assoc_res_name = 'fake_resource'
    _resource = '%s_association' % _assoc_res_name
    _resource_plural = '%ss' % _resource

    _attr_map = (
        ('id', 'ID', column_util.LIST_BOTH),
        ('%s_id' % _assoc_res_name, '%s ID' % _assoc_res_name.capitalize(),
         column_util.LIST_BOTH),
        ('name', 'Name', column_util.LIST_BOTH),
        ('project_id', 'Project ID', column_util.LIST_BOTH),
    )
    _formatters = {}


class CreateBgpvpnFakeResAssoc(BgpvpnFakeAssoc, CreateBgpvpnResAssoc):
    pass


class SetBgpvpnFakeResAssoc(BgpvpnFakeAssoc, SetBgpvpnResAssoc):
    pass


class UnsetBgpvpnFakeResAssoc(BgpvpnFakeAssoc, UnsetBgpvpnResAssoc):
    pass


class DeleteBgpvpnFakeResAssoc(BgpvpnFakeAssoc, DeleteBgpvpnResAssoc):
    pass


class ListBgpvpnFakeResAssoc(BgpvpnFakeAssoc, ListBgpvpnResAssoc):
    pass


class ShowBgpvpnFakeResAssoc(BgpvpnFakeAssoc, ShowBgpvpnResAssoc):
    pass


class BgpvpnFakeRouterAssoc(object):
    _assoc_res_name = 'fake_resource'
    _resource = '%s_association' % _assoc_res_name
    _resource_plural = '%ss' % _resource

    _attr_map = (
        ('id', 'ID', column_util.LIST_BOTH),
        ('%s_id' % _assoc_res_name, '%s ID' % _assoc_res_name.capitalize(),
         column_util.LIST_BOTH),
        ('advertise_extra_routes', 'Advertise extra routes',
         column_util.LIST_LONG_ONLY),
        ('name', 'Name', column_util.LIST_BOTH),
        ('project_id', 'Project ID', column_util.LIST_BOTH),
    )
    _formatters = {}


class CreateBgpvpnFakeRouterAssoc(BgpvpnFakeRouterAssoc,
                                  CreateBgpvpnRouterAssoc):
    pass


class SetBgpvpnFakeRouterAssoc(BgpvpnFakeRouterAssoc, SetBgpvpnRouterAssoc):
    pass


class ShowBgpvpnFakeRouterAssoc(BgpvpnFakeRouterAssoc, ShowBgpvpnRouterAssoc):
    pass


class FakeResource(sdk_resource.Resource):
    resource_key = 'fakeresource'
    resources_key = 'fakeresources'
    base_path = '/bgpvpn/fakeresources'

    _allow_unknown_attrs_in_body = True

    # capabilities
    allow_create = True
    allow_fetch = True
    allow_commit = True
    allow_delete = True
    allow_list = True

    id = sdk_resource.Body('id')
    tenant_id = sdk_resource.Body('tenant_id', deprecated=True)
    project_id = sdk_resource.Body('project_id', alias='tenant_id')


class FakeResoureAssociation(sdk_resource.Resource):
    resource_key = 'fakeresourceassociation'
    resources_key = 'fakeresourceassociations'
    base_path = '/bgpvpn/fakeresourceassociations'

    _allow_unknown_attrs_in_body = True

    # capabilities
    allow_create = True
    allow_fetch = True
    allow_commit = True
    allow_delete = True
    allow_list = True

    id = sdk_resource.Body('id')
    tenant_id = sdk_resource.Body('tenant_id', deprecated=True)
    project_id = sdk_resource.Body('project_id', alias='tenant_id')


def create_one_resource(attrs=None):
    """Create a fake resource."""
    attrs = attrs or {}

    # Set default attributes.
    res_attrs = {
        'id': 'fake_resource_id',
        'tenant_id': _FAKE_PROJECT_ID,
    }

    # Overwrite default attributes.
    res_attrs.update(attrs)
    return FakeResource(**res_attrs)


def create_resources(attrs=None, count=1):
    """Create multiple fake resources."""

    resources = []
    for i in range(0, count):
        if attrs is None:
            attrs = {'id': 'fake_id%d' % i}
        elif getattr(attrs, 'id', None) is None:
            attrs['id'] = 'fake_id%d' % i
        resources.append(create_one_resource(attrs))

    return resources


def create_one_resource_association(resource, attrs=None):
    """Create a fake resource association."""

    attrs = attrs or {}

    res_assoc_attrs = {
        'id': 'fake_association_id',
        'tenant_id': resource['tenant_id'],
        'fake_resource_id': resource['id'],
    }

    # Overwrite default attributes.
    res_assoc_attrs.update(attrs)
    return FakeResoureAssociation(**res_assoc_attrs)


def create_resource_associations(resources):
    """Create multiple fake resource associations."""

    res_assocs = []
    for idx, resource in enumerate(resources):
        res_assoc_attrs = {
            'id': 'fake_association_id%d' % idx,
            'tenant_id': resource['tenant_id'],
            'fake_resource_id': resource['id'],
        }
        res_assocs.append(copy.deepcopy(res_assoc_attrs))

    return res_assocs
