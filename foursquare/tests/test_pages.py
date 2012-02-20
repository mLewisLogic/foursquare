#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2012 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEnpdointTestCase, BaseUserlessEnpdointTestCase



class VenuesEndpointTestCase(BaseAuthenticatedEnpdointTestCase):
    """
    General
    """
    def test_pages(self):
        response = self.api.pages(self.default_userid)
        assert 'user' in response


    def test_search(self):
        response = self.api.pages.search({'name': 'Starbucks'})
        assert 'results' in response


    def test_venues(self):
        response = self.api.pages.venues(self.default_pageid)
        assert 'venues' in response



class VenuesUserlessEndpointTestCase(BaseUserlessEnpdointTestCase):
    """
    General
    """
    def test_pages(self):
        response = self.api.pages(self.default_userid)
        assert 'user' in response


    def test_search(self):
        response = self.api.pages.search({'name': 'Starbucks'})
        assert 'results' in response


    def test_venues(self):
        response = self.api.pages.venues(self.default_pageid)
        assert 'venues' in response
