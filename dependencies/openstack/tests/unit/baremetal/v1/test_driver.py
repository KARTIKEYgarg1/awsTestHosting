# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from unittest import mock

from keystoneauth1 import adapter

from openstack.baremetal.v1 import _common
from openstack.baremetal.v1 import driver
from openstack import exceptions
from openstack.tests.unit import base


FAKE = {
    "hosts": ["897ab1dad809"],
    "links": [
        {
            "href": "http://127.0.0.1:6385/v1/drivers/agent_ipmitool",
            "rel": "self",
        },
        {
            "href": "http://127.0.0.1:6385/drivers/agent_ipmitool",
            "rel": "bookmark",
        },
    ],
    "name": "agent_ipmitool",
    "properties": [
        {
            "href": "http://127.0.0.1:6385/v1/drivers/agent_ipmitool/properties",  # noqa: E501
            "rel": "self",
        },
        {
            "href": "http://127.0.0.1:6385/drivers/agent_ipmitool/properties",
            "rel": "bookmark",
        },
    ],
}


class TestDriver(base.TestCase):
    def test_basic(self):
        sot = driver.Driver()
        self.assertIsNone(sot.resource_key)
        self.assertEqual('drivers', sot.resources_key)
        self.assertEqual('/drivers', sot.base_path)
        self.assertFalse(sot.allow_create)
        self.assertTrue(sot.allow_fetch)
        self.assertFalse(sot.allow_commit)
        self.assertFalse(sot.allow_delete)
        self.assertTrue(sot.allow_list)

    def test_instantiate(self):
        sot = driver.Driver(**FAKE)
        self.assertEqual(FAKE['name'], sot.id)
        self.assertEqual(FAKE['name'], sot.name)
        self.assertEqual(FAKE['hosts'], sot.hosts)
        self.assertEqual(FAKE['links'], sot.links)
        self.assertEqual(FAKE['properties'], sot.properties)

    @mock.patch.object(exceptions, 'raise_from_response', mock.Mock())
    def test_list_vendor_passthru(self):
        self.session = mock.Mock(spec=adapter.Adapter)
        sot = driver.Driver(**FAKE)
        fake_vendor_passthru_info = {
            'fake_vendor_method': {
                'async': True,
                'attach': False,
                'description': "Fake function that does nothing in background",
                'http_methods': ['GET', 'PUT', 'POST', 'DELETE'],
            }
        }
        self.session.get.return_value.json.return_value = (
            fake_vendor_passthru_info
        )
        result = sot.list_vendor_passthru(self.session)
        self.session.get.assert_called_once_with(
            'drivers/{driver_name}/vendor_passthru/methods'.format(
                driver_name=FAKE["name"]
            ),
            headers=mock.ANY,
        )
        self.assertEqual(result, fake_vendor_passthru_info)

    @mock.patch.object(exceptions, 'raise_from_response', mock.Mock())
    def test_call_vendor_passthru(self):
        self.session = mock.Mock(spec=adapter.Adapter)
        sot = driver.Driver(**FAKE)
        # GET
        sot.call_vendor_passthru(self.session, 'GET', 'fake_vendor_method')
        self.session.get.assert_called_once_with(
            'drivers/{}/vendor_passthru?method={}'.format(
                FAKE["name"], 'fake_vendor_method'
            ),
            json=None,
            headers=mock.ANY,
            retriable_status_codes=_common.RETRIABLE_STATUS_CODES,
        )
        # PUT
        sot.call_vendor_passthru(
            self.session,
            'PUT',
            'fake_vendor_method',
            body={"fake_param_key": "fake_param_value"},
        )
        self.session.put.assert_called_once_with(
            'drivers/{}/vendor_passthru?method={}'.format(
                FAKE["name"], 'fake_vendor_method'
            ),
            json={"fake_param_key": "fake_param_value"},
            headers=mock.ANY,
            retriable_status_codes=_common.RETRIABLE_STATUS_CODES,
        )
        # POST
        sot.call_vendor_passthru(
            self.session,
            'POST',
            'fake_vendor_method',
            body={"fake_param_key": "fake_param_value"},
        )
        self.session.post.assert_called_once_with(
            'drivers/{}/vendor_passthru?method={}'.format(
                FAKE["name"], 'fake_vendor_method'
            ),
            json={"fake_param_key": "fake_param_value"},
            headers=mock.ANY,
            retriable_status_codes=_common.RETRIABLE_STATUS_CODES,
        )
        # DELETE
        sot.call_vendor_passthru(self.session, 'DELETE', 'fake_vendor_method')
        self.session.delete.assert_called_once_with(
            'drivers/{}/vendor_passthru?method={}'.format(
                FAKE["name"], 'fake_vendor_method'
            ),
            json=None,
            headers=mock.ANY,
            retriable_status_codes=_common.RETRIABLE_STATUS_CODES,
        )
