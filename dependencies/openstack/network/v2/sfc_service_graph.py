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

from openstack import resource


class SfcServiceGraph(resource.Resource):
    resource_key = 'service_graph'
    resources_key = 'service_graphs'
    base_path = '/sfc/service_graphs'

    # capabilities
    allow_create = True
    allow_fetch = True
    allow_commit = True
    allow_delete = True
    allow_list = True

    _query_mapping = resource.QueryParameters(
        'description',
        'name',
        'project_id',
        'tenant_id',
    )

    # Properties
    #: Human-readable description for the resource.
    description = resource.Body('description')
    #: Human-readable name of the resource. Default is an empty string.
    name = resource.Body('name')
    #: A dictionary where the key is the source port chain and the
    #: value is a list of destination port chains.
    port_chains = resource.Body('port_chains')
    project_id = resource.Body('project_id', alias='tenant_id')
    #: Tenant_id (deprecated attribute).
    tenant_id = resource.Body('tenant_id', deprecated=True)
