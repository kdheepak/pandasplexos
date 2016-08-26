# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow)

import logging

from lxml import etree
import pandas as pd

from .helper import elem2dict

logger = logging.getLogger(__name__)
NAMESPACES = {'n': 'http://tempuri.org/SolutionDataset.xsd'}


class PandasPlexosSolution(object):
    def __init__(self, input_file):
        with open(input_file) as f:
            data = f.read()

        self._root = etree.fromstring(data)
        self._tables = tuple({element.tag.replace('{{{}}}'.format(NAMESPACES['n']), '') for element in self._root.getchildren()})
        for tbl in self._tables:
            self._create_property(tbl)

    def _create_property(self, prop):
        is_index_set = False
        lst = []
        for element in self._root.xpath('n:{}'.format(prop), namespaces=NAMESPACES):
            dct = elem2dict(element)
            lst.append(dct)
        df = pd.DataFrame(lst)

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

        setattr(self, prop, df)
