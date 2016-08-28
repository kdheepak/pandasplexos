# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow)

import logging
import os
import zipfile

try:
    from lxml import etree
except ImportError:
    from xml import etree

import pandas as pd
import numpy as np

from .helper import elem2dict

logger = logging.getLogger(__name__)
NAMESPACES = {'n': 'http://tempuri.org/SolutionDataset.xsd'}


class PandasPlexosSolution(object):
    def __init__(self, file):

        self._extract_metainformation(file)
        self._generate_tables()
        # self._read_binary()

    def _extract_metainformation(self, file):
        archive = zipfile.ZipFile(file, 'r')
        self._bin_files = {}
        for file in archive.namelist():
            if '.xml' in file:
                data = archive.read(file)
                self._root = etree.fromstring(data)
            if '.bin' in file.lower():
                self._bin_files[file] = np.frombuffer(archive.read(file), dtype=float)

    def _generate_tables(self):
        self._tables = tuple({element.tag.replace('{{{}}}'.format(NAMESPACES['n']), '') for element in self._root.getchildren()})
        for tbl in self._tables:
            self._create_property(tbl)
        self._create_temp()

    def _create_property(self, prop):
        lst = []
        for element in self._root.xpath('n:{}'.format(prop), namespaces=NAMESPACES):
            dct = elem2dict(element)
            lst.append(dct)
        df = pd.DataFrame(lst)
        setattr(self, prop, df)

    def _create_temp(self):
        self.__temp_class()
        self.__temp_object()
        self.__temp_property()
        self.__temp_membership()
        self.__temp_zone_id()
        self.__temp_zones()
        self.__temp_key()
        self.__temp_phase()

    def __temp_class(self):

        temp_class = pd.merge(self.t_class.drop('lang_id', axis=1),
                         self.t_class_group.drop('lang_id', axis=1),
                         on='class_group_id')
        temp_class.rename(columns={'name_x': 'class', 'name_y': 'class_group'}, inplace=True)
        self._temp_class = temp_class

    def __temp_object(self):

        df = pd.merge(self.t_object, self._temp_class, on='class_id')
        temp_object = pd.merge(df, self.t_category, on='category_id')
        temp_object.rename(columns={'name_x': 'name',
                                    'name_y': 'category'}, inplace=True)
        self._temp_object = temp_object[['object_id', 'name', 'category', 'class', 'class_group']]

    def __temp_property(self):
        df = pd.merge(self.t_property, self.t_collection, on='collection_id')

        temp_property1 = pd.merge(df, self.t_unit, on='unit_id')

        temp_property1.rename(columns={'name_x': 'property',
                                      'name_y': 'collection',
                                      'value': 'unit'}, inplace=True)

        temp_property1['period_type_id'] = '0'

        temp_property1 = temp_property1[['property_id',
                       'period_type_id',
                       'property',
                       'collection',
                       'unit']]

        temp_property2 = pd.merge(df, self.t_unit,
                                  left_on='summary_unit_id',
                                  right_on='unit_id')

        temp_property2.rename(columns={'name_x': 'property',
                                      'name_y': 'collection',
                                      'value': 'unit'}, inplace=True)

        temp_property2['period_type_id'] = '1'

        temp_property2 = temp_property2[['property_id',
                       'period_type_id',
                       'property',
                       'collection',
                       'unit']]

        temp_property = pd.concat([temp_property1, temp_property2], ignore_index=True)

        self._temp_property = temp_property

    def __temp_membership(self):
        df = pd.merge(self.t_membership, self.t_collection, on='collection_id')

        df = pd.merge(df, self._temp_object,
                 left_on='parent_object_id',
                 right_on='object_id')

        df = pd.merge(df, self._temp_object,
                left_on='child_object_id',
                right_on='object_id')

        df.rename(columns={'name_x': 'collection',
                           'name_y': 'parent_name',
                           'name': 'child_name',
                           'class_x': 'parent_class',
                           'class_group_x': 'parent_group',
                           'category_x': 'parent_category',
                           'class_y': 'child_class',
                           'class_group_y': 'child_group',
                           'category_y': 'child_category',
                           }, inplace=True)

        df = df[['membership_id',
            'parent_object_id',
            'child_object_id',
            'collection',
            'parent_name',
            'parent_class',
            'parent_group',
            'parent_category',
            'child_name',
            'child_class',
            'child_group',
            'child_category']]

        df = self._sort_values_by_key(df, 'membership_id')

        self._temp_membership = df

    def __temp_zone_id(self):
        df = self._temp_membership[(self._temp_membership['collection'] == 'Generators') &
                             (self._temp_membership['parent_class'] == 'Region')]

        df = df[['child_object_id', 'parent_object_id']]

        # NOTE : min is being performed on string attribute
        # Although this works, this could have unintended consequences
        df['parent_object_id'] = df['parent_object_id'].min()

        self._temp_zone_id = df

    def __temp_zones(self):
        df = pd.merge(self._temp_zone_id, self._temp_object,
                 left_on='parent_object_id',
                 right_on='object_id')

        df.rename(columns={'name': 'region',
                          'category': 'zone'}, inplace=True)

        df = df[['child_object_id', 'region', 'zone']]

        self._temp_zones = df

    def __temp_key(self):
        df = pd.merge(self.t_key, self._temp_membership, on='membership_id')
        df = pd.merge(df, self.t_timeslice, on='timeslice_id')
        df = pd.merge(df, self._temp_property, on=['property_id', 'period_type_id'])
        df = pd.merge(df, self._temp_zones, on='child_object_id', how='left')

        df.rename(columns={'key_id': 'key',
                          'collection_x': 'child_collection',
                          'name': 'timeslice',
                          'band_id': 'band',
                          'sample_id': 'sample'}, inplace=True)
        df['zone'].fillna('', inplace=True)
        df['region'].fillna('', inplace=True)

        is_parent_class_system = df['parent_class'] == "System"
        df.ix[is_parent_class_system, 'collection'] = df[is_parent_class_system]['child_class']
        df.ix[~is_parent_class_system, 'collection'] = df[~is_parent_class_system]['parent_class'] + '.' + df[~is_parent_class_system]['child_collection']
        df['table_name'] = 'data_interval_' + df['collection'] + '_' + df['property']
        df['table_name'] = df['table_name'].apply(lambda x: x.replace(' ', ''))

        def func(x):
            x=x.replace('0', 'Mean')
            x=x.replace('1', 'StDev')
            x=x.replace('2', 'Min')
            x=x.replace('3', 'Max')
            return x
        df['sample'] = df['sample'].apply(func)

        df = df[['key',
            'table_name',
            'collection',
            'property',
            'unit',
            'child_name',
            'parent_name',
            'child_category',
            'region',
            'zone',
            'child_class',
            'child_group',
            'phase_id',
            'period_type_id',
            'timeslice',
            'band',
            'sample']]

        df.rename(columns={'child_name': 'name',
                          'parent_name': 'parent',
                          'child_category': 'category',
                          'child_class': 'class',
                           'child_group': 'class_group'}, inplace=True)

        df = self._sort_values_by_key(df, 'key')

        self._temp_key = df

    def __temp_phase(self):
        for phase in range(0, 4):
            try:
                df = pd.merge(self.t_period_0, getattr(self, 't_phase_{}'.format(phase + 1)), on='interval_id', how='inner')
                df['datetime'] = pd.to_datetime(df['datetime'])
                setattr(self, '_temp_phase_{}'.format(phase + 1), df)
            except AttributeError as e:
                logger.debug(e)

    def _assertions(self):
        assert(len(self._temp_key['key']) == len(self.t_key['key_id']))

    @classmethod
    def _sort_values_by_key(cls, df, key):

        df[key] = df[key].apply(lambda x: int(x))
        df = df.sort_values(by=key)
        df[key] = df[key].apply(lambda x: str(x))
        df.reset_index(drop=True, inplace=True)

        return(df)
