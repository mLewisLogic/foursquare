#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2014 Mike Lewis
import logging; log = logging.getLogger(__name__)

from . import BaseAuthenticatedEndpointTestCase, BaseUserlessEndpointTestCase



class VenuesEndpointTestCase(BaseAuthenticatedEndpointTestCase):
    """
    General
    """
    def test_pages(self):
        response = self.api.pages(self.default_userid)
        assert 'user' in response


    def test_venues(self):
        response = self.api.pages.venues(self.default_pageid)
        assert 'venues' in response



class VenuesUserlessEndpointTestCase(BaseUserlessEndpointTestCase):
    """
    General
    """
    def test_pages(self):
        response = self.api.pages(self.default_userid)
        assert 'user' in response


    def test_venues(self):
        response = self.api.pages.venues(self.default_pageid)
        assert 'venues' in response
