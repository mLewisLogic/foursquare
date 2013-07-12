#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2013 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import MultilangEndpointTestCase



class MultiLangTestCase(MultilangEndpointTestCase):
    """
    General
    """
    def test_lang(self):
        """Test a wide swath of languages"""
        for api in self.apis:
            categories = api.venues.categories()
            assert 'categories' in categories, u"'categories' not in response"
            assert len(categories['categories']) > 1, u'Expected multiple categories'
