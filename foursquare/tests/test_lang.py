#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

import foursquare

try:
    from . import _creds
except ImportError:
    print "Please create a creds.py file in this package, based upon creds.example.py"

from . import BaseEndpointTestCase



class MultiLangTestCase(BaseEndpointTestCase):
    """
    General
    """
    def test_lang(self):
        """Test a wide swath of languages"""
        for lang in ('es', 'fr', 'de', 'it', 'ja', 'th', 'ko', 'ru', 'pt', 'id'):
            client = foursquare.Foursquare(
                client_id=_creds.CLIENT_ID,
                client_secret=_creds.CLIENT_SECRET,
                lang=lang
            )
            categories = client.venues.categories()
            assert 'categories' in categories, u"'categories' not in response"
            assert len(categories['categories']) > 1, u'Expected multiple categories'
