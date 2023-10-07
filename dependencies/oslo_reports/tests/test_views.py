# Copyright 2013 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
from unittest import mock

from oslotest import base

from oslo_reports.models import base as base_model
from oslo_reports.models import with_default_views as mwdv
from oslo_reports import report
from oslo_reports.views import jinja_view as jv
from oslo_reports.views.json import generic as json_generic
from oslo_reports.views.text import generic as text_generic


def mwdv_generator():
    return mwdv.ModelWithDefaultViews(data={'string': 'value', 'int': 1})


class TestModelReportType(base.BaseTestCase):
    def test_model_with_default_views(self):
        model = mwdv_generator()

        model.set_current_view_type('text')
        self.assertEqual('int = 1\nstring = value', str(model))

        model.set_current_view_type('json')
        self.assertEqual('{"int": 1, "string": "value"}', str(model))

        model.set_current_view_type('xml')

        self.assertEqual('<model><int>1</int><string>value</string></model>',
                         str(model))

    def test_recursive_type_propagation_with_nested_models(self):
        model = mwdv_generator()
        model['submodel'] = mwdv_generator()

        model.set_current_view_type('json')

        self.assertEqual(model.submodel.views['json'],
                         model.submodel.attached_view)

    def test_recursive_type_propagation_with_nested_dicts(self):
        nested_model = mwdv.ModelWithDefaultViews(json_view='abc')
        data = {'a': 1, 'b': {'c': nested_model}}
        top_model = base_model.ReportModel(data=data)

        top_model.set_current_view_type('json')
        self.assertEqual(nested_model.attached_view,
                         nested_model.views['json'])

    def test_recursive_type_propagation_with_nested_lists(self):
        nested_model = mwdv_generator()
        data = {'a': 1, 'b': [nested_model]}
        top_model = base_model.ReportModel(data=data)

        top_model.set_current_view_type('json')
        self.assertEqual(nested_model.attached_view,
                         nested_model.views['json'])

    def test_recursive_type_propogation_on_recursive_structures(self):
        nested_model = mwdv_generator()
        data = {'a': 1, 'b': [nested_model]}
        nested_model['c'] = data
        top_model = base_model.ReportModel(data=data)

        top_model.set_current_view_type('json')
        self.assertEqual(nested_model.attached_view,
                         nested_model.views['json'])
        del nested_model['c']

    def test_report_of_type(self):
        rep = report.ReportOfType('json')
        rep.add_section(lambda x: str(x), mwdv_generator)

        self.assertEqual('{"int": 1, "string": "value"}', rep.run())

    # NOTE: this also tests views.text.header
    def test_text_report(self):
        rep = report.TextReport('Test Report')
        rep.add_section('An Important Section', mwdv_generator)
        rep.add_section('Another Important Section', mwdv_generator)

        target_str = ('========================================================================\n'  # noqa
                      '====                          Test Report                           ====\n'  # noqa
                      '========================================================================\n'  # noqa
                      '||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||\n'  # noqa
                      '\n'                                                                          # noqa
                      '\n'                                                                          # noqa
                      '========================================================================\n'  # noqa
                      '====                      An Important Section                      ====\n'  # noqa
                      '========================================================================\n'  # noqa
                      'int = 1\n'                                                                   # noqa
                      'string = value\n'                                                            # noqa
                      '========================================================================\n'  # noqa
                      '====                   Another Important Section                    ====\n'  # noqa
                      '========================================================================\n'  # noqa
                      'int = 1\n'                                                                   # noqa
                      'string = value')                                                             # noqa
        self.assertEqual(target_str, rep.run())

    def test_to_type(self):
        model = mwdv_generator()

        self.assertEqual('<model><int>1</int><string>value</string></model>',
                         model.to_xml())


class TestGenericXMLView(base.BaseTestCase):
    def setUp(self):
        super(TestGenericXMLView, self).setUp()

        self.model = mwdv_generator()
        self.model.set_current_view_type('xml')

    def test_dict_serialization(self):
        self.model['dt'] = {'a': 1, 'b': 2}

        target_str = ('<model>'
                      '<dt><a>1</a><b>2</b></dt>'
                      '<int>1</int>'
                      '<string>value</string></model>')
        self.assertEqual(target_str, str(self.model))

    def test_list_serialization(self):
        self.model['lt'] = ['a', 'b']

        target_str = ('<model>'
                      '<int>1</int>'
                      '<lt><item>a</item><item>b</item></lt>'
                      '<string>value</string></model>')
        self.assertEqual(target_str, str(self.model))

    def test_list_in_dict_serialization(self):
        self.model['dt'] = {'a': 1, 'b': [2, 3]}

        target_str = ('<model>'
                      '<dt><a>1</a>'
                      '<b><item>2</item><item>3</item></b></dt>'
                      '<int>1</int>'
                      '<string>value</string></model>')
        self.assertEqual(target_str, str(self.model))

    def test_dict_in_list_serialization(self):
        self.model['lt'] = [1, {'b': 2, 'c': 3}]

        target_str = ('<model>'
                      '<int>1</int>'
                      '<lt><item>1</item>'
                      '<item><b>2</b><c>3</c></item></lt>'
                      '<string>value</string></model>')
        self.assertEqual(target_str, str(self.model))

    def test_submodel_serialization(self):
        sm = mwdv_generator()
        sm.set_current_view_type('xml')

        self.model['submodel'] = sm

        target_str = ('<model>'
                      '<int>1</int>'
                      '<string>value</string>'
                      '<submodel>'
                      '<model><int>1</int><string>value</string></model>'
                      '</submodel>'
                      '</model>')
        self.assertEqual(target_str, str(self.model))

    def test_wrapper_name(self):
        self.model.attached_view.wrapper_name = 'cheese'

        target_str = ('<cheese>'
                      '<int>1</int>'
                      '<string>value</string>'
                      '</cheese>')
        self.assertEqual(target_str, str(self.model))


class TestGenericJSONViews(base.BaseTestCase):
    def setUp(self):
        super(TestGenericJSONViews, self).setUp()

        self.model = mwdv_generator()
        self.model.set_current_view_type('json')

    def test_basic_kv_view(self):
        attached_view = json_generic.BasicKeyValueView()
        self.model = base_model.ReportModel(data={'string': 'value', 'int': 1},
                                            attached_view=attached_view)

        self.assertEqual('{"int": 1, "string": "value"}',
                         str(self.model))

    def test_dict_serialization(self):
        self.model['dt'] = {'a': 1, 'b': 2}

        target_str = ('{'
                      '"dt": {"a": 1, "b": 2}, '
                      '"int": 1, '
                      '"string": "value"'
                      '}')
        self.assertEqual(target_str, str(self.model))

    def test_list_serialization(self):
        self.model['lt'] = ['a', 'b']

        target_str = ('{'
                      '"int": 1, '
                      '"lt": ["a", "b"], '
                      '"string": "value"'
                      '}')
        self.assertEqual(target_str, str(self.model))

    def test_list_in_dict_serialization(self):
        self.model['dt'] = {'a': 1, 'b': [2, 3]}

        target_str = ('{'
                      '"dt": {"a": 1, "b": [2, 3]}, '
                      '"int": 1, '
                      '"string": "value"'
                      '}')
        self.assertEqual(target_str, str(self.model))

    def test_dict_in_list_serialization(self):
        self.model['lt'] = [1, {'b': 2, 'c': 3}]

        target_str = ('{'
                      '"int": 1, '
                      '"lt": [1, {"b": 2, "c": 3}], '
                      '"string": "value"'
                      '}')
        self.assertEqual(target_str, str(self.model))

    def test_submodel_serialization(self):
        sm = mwdv_generator()
        sm.set_current_view_type('json')

        self.model['submodel'] = sm

        target_str = ('{'
                      '"int": 1, '
                      '"string": "value", '
                      '"submodel": {"int": 1, "string": "value"}'
                      '}')
        self.assertEqual(target_str, str(self.model))


class TestGenericTextViews(base.BaseTestCase):
    def setUp(self):
        super(TestGenericTextViews, self).setUp()

        self.model = mwdv_generator()
        self.model.set_current_view_type('text')

    def test_multi_view(self):
        attached_view = text_generic.MultiView()
        self.model = base_model.ReportModel(data={},
                                            attached_view=attached_view)

        self.model['1'] = mwdv_generator()
        self.model['2'] = mwdv_generator()
        self.model['2']['int'] = 2
        self.model.set_current_view_type('text')

        target_str = ('int = 1\n'
                      'string = value\n'
                      'int = 2\n'
                      'string = value')
        self.assertEqual(target_str, str(self.model))

    def test_basic_kv_view(self):
        attached_view = text_generic.BasicKeyValueView()
        self.model = base_model.ReportModel(data={'string': 'value', 'int': 1},
                                            attached_view=attached_view)

        self.assertEqual('int = 1\nstring = value\n',
                         str(self.model))

    def test_table_view(self):
        column_names = ['Column A', 'Column B']
        column_values = ['a', 'b']
        attached_view = text_generic.TableView(column_names, column_values,
                                               'table')
        self.model = base_model.ReportModel(data={},
                                            attached_view=attached_view)

        self.model['table'] = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]

        target_str = ('             Column A              |             Column B               \n'   # noqa
                      '------------------------------------------------------------------------\n'   # noqa
                      '                 1                 |                 2                  \n'   # noqa
                      '                 3                 |                 4                  \n')  # noqa

        self.assertEqual(target_str, str(self.model))

    def test_dict_serialization(self):
        self.model['dt'] = {'a': 1, 'b': 2}

        target_str = ('dt = \n'
                      '  a = 1\n'
                      '  b = 2\n'
                      'int = 1\n'
                      'string = value')
        self.assertEqual(target_str, str(self.model))

    def test_dict_serialization_integer_keys(self):
        self.model['dt'] = {3: 4, 5: 6}

        target_str = ('dt = \n'
                      '  3 = 4\n'
                      '  5 = 6\n'
                      'int = 1\n'
                      'string = value')
        self.assertEqual(target_str, str(self.model))

    def test_dict_serialization_mixed_keys(self):
        self.model['dt'] = {'3': 4, 5: 6}

        target_str = ('dt = \n'
                      '  3 = 4\n'
                      '  5 = 6\n'
                      'int = 1\n'
                      'string = value')
        self.assertEqual(target_str, str(self.model))

    def test_list_serialization(self):
        self.model['lt'] = ['a', 'b']

        target_str = ('int = 1\n'
                      'lt = \n'
                      '  a\n'
                      '  b\n'
                      'string = value')
        self.assertEqual(target_str, str(self.model))

    def test_list_in_dict_serialization(self):
        self.model['dt'] = {'a': 1, 'b': [2, 3]}

        target_str = ('dt = \n'
                      '  a = 1\n'
                      '  b = \n'
                      '    2\n'
                      '    3\n'
                      'int = 1\n'
                      'string = value')

        self.assertEqual(target_str, str(self.model))

    def test_dict_in_list_serialization(self):
        self.model['lt'] = [1, {'b': 2, 'c': 3}]

        target_str = ('int = 1\n'
                      'lt = \n'
                      '  1\n'
                      '  [dict]\n'
                      '    b = 2\n'
                      '    c = 3\n'
                      'string = value')
        self.assertEqual(target_str, str(self.model))

    def test_submodel_serialization(self):
        sm = mwdv_generator()
        sm.set_current_view_type('text')

        self.model['submodel'] = sm

        target_str = ('int = 1\n'
                      'string = value\n'
                      'submodel = \n'
                      '  int = 1\n'
                      '  string = value')
        self.assertEqual(target_str, str(self.model))

    def test_custom_indent_string(self):
        view = text_generic.KeyValueView(indent_str='~~')

        self.model['lt'] = ['a', 'b']
        self.model.attached_view = view

        target_str = ('int = 1\n'
                      'lt = \n'
                      '~~a\n'
                      '~~b\n'
                      'string = value')
        self.assertEqual(target_str, str(self.model))


def get_open_mocks(rv):
    file_mock = mock.MagicMock(name='file_obj')
    file_mock.read.return_value = rv
    open_mock = mock.MagicMock(name='open')
    open_mock().__enter__.return_value = file_mock
    return (open_mock, file_mock)


class TestJinjaView(base.BaseTestCase):

    TEMPL_STR = "int is {{ int }}, string is {{ string }}"
    MM_OPEN, MM_FILE = get_open_mocks(TEMPL_STR)

    def setUp(self):
        super(TestJinjaView, self).setUp()
        self.model = base_model.ReportModel(data={'int': 1, 'string': 'value'})

    @mock.mock_open(MM_OPEN)
    def test_load_from_file(self):
        self.model.attached_view = jv.JinjaView(path='a/b/c/d.jinja.txt')

        self.assertEqual('int is 1, string is value',
                         str(self.model))
        self.MM_FILE.assert_called_with_once('a/b/c/d.jinja.txt')

    def test_direct_pass(self):
        self.model.attached_view = jv.JinjaView(text=self.TEMPL_STR)

        self.assertEqual('int is 1, string is value',
                         str(self.model))

    def test_load_from_class(self):
        class TmpJinjaView(jv.JinjaView):
            VIEW_TEXT = TestJinjaView.TEMPL_STR

        self.model.attached_view = TmpJinjaView()

        self.assertEqual('int is 1, string is value',
                         str(self.model))

    def test_is_deepcopiable(self):
        view_orig = jv.JinjaView(text=self.TEMPL_STR)
        view_cpy = copy.deepcopy(view_orig)

        self.assertIsNot(view_orig, view_cpy)
