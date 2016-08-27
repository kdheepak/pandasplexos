# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow)

import logging
import os

try:
    from lxml import etree
except ImportError:
    from xml import etree

import pandas as pd

from .helper import elem2dict

logger = logging.getLogger(__name__)
NAMESPACES = {'n': 'http://tempuri.org/SolutionDataset.xsd'}


class PandasPlexosSolution(object):
    def __init__(self, file):

        try:
            self._root = etree.fromstring(file)
        except IOError:
            with open(os.path.abspath(file)) as f:
                data = f.read()
            self._root = etree.fromstring(data)

        self._tables = tuple({element.tag.replace('{{{}}}'.format(NAMESPACES['n']), '') for element in self._root.getchildren()})
        for tbl in self._tables:
            self._create_property(tbl)

    def _create_property(self, prop):
        lst = []
        for element in self._root.xpath('n:{}'.format(prop), namespaces=NAMESPACES):
            dct = elem2dict(element)
            lst.append(dct)
        df = pd.DataFrame(lst)
        df = self._try_set_index(df, prop)
        setattr(self, prop, df)

    def _try_set_index(self, df, prop):
        is_index_set = False
        if not is_index_set:
            try:
                df = df.set_index('{}_id'.format(prop.replace('t_', '')))
                is_index_set = True
            except KeyError:
                is_index_set = False

        if not is_index_set:
            try:
                df = df.set_index('{}_id'.format(prop.replace('t_', '').replace('_index', '')))
                is_index_set = True
            except KeyError:
                is_index_set = False

        if not is_index_set:
            try:
                df = df.set_index('date')
                df.index = pd.to_datetime(df.index)
                is_index_set = True
            except KeyError:
                is_index_set = False

        if not is_index_set:
            try:
                df = df.set_index('datetime')
                df.index = pd.to_datetime(df.index)
                is_index_set = True
            except KeyError:
                is_index_set = False

        if not is_index_set:
            logger.debug("Unable to set index for {}".format(prop))

        return df
